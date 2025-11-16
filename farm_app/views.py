import os
import tempfile
from datetime import datetime
import json
import requests

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages

from .forms import UserRegisterForm, CropForm
from .models import Crop
from .aws_utils import upload_file_to_s3, send_analysis_message_to_sqs

from smartfarmcrophealth import CropHealthAnalyzer


def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'farm_app/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    else:
        form = AuthenticationForm()
    return render(request, 'farm_app/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    crops = Crop.objects.all().order_by('-created_at')
    return render(request, 'farm_app/dashboard.html', {'crops': crops})


@login_required
def crop_create_view(request):
    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES)
        if form.is_valid():
            crop = form.save(commit=False)
            crop.user = request.user
            crop.save()

            # Upload image to S3 after saving locally
            local_path = crop.image.path
            s3_key = f"user_{request.user.id}/crops/{os.path.basename(local_path)}"
            s3_url = upload_file_to_s3(local_path, s3_key)
            crop.s3_image_url = s3_url
            crop.save()

            messages.success(request, 'Crop created successfully.')
            return redirect('dashboard')
    else:
        form = CropForm()
    return render(request, 'farm_app/crop_form.html', {'form': form, 'title': 'Create Crop'})


@login_required
def crop_update_view(request, pk):
    crop = get_object_or_404(Crop, pk=pk)

    if crop.user != request.user:
        messages.error(request, "You cannot edit another user's crop.")
        return redirect('crop_detail', pk=pk)

    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES, instance=crop)
        if form.is_valid():
            crop = form.save()

            if 'image' in form.changed_data:
                local_path = crop.image.path
                s3_key = f"user_{request.user.id}/crops/{os.path.basename(local_path)}"
                s3_url = upload_file_to_s3(local_path, s3_key)
                crop.s3_image_url = s3_url
                crop.status = 'pending'
                crop.analyzed_result = None
                crop.analyzed_at = None
                crop.save()

            messages.success(request, 'Crop updated successfully.')
            return redirect('crop_detail', pk=pk)
    else:
        form = CropForm(instance=crop)

    return render(request, 'farm_app/crop_form.html', {'form': form, 'title': 'Update Crop'})


@login_required
def crop_delete_view(request, pk):
    crop = get_object_or_404(Crop, pk=pk)

    if crop.user != request.user:
        messages.error(request, "You cannot delete another user's crop.")
        return redirect('crop_detail', pk=pk)

    if request.method == 'POST':
        crop.delete()
        messages.success(request, 'Crop deleted successfully.')
        return redirect('dashboard')

    return render(request, 'farm_app/crop_confirm_delete.html', {'crop': crop})



@login_required
def crop_detail_view(request, pk):
    crop = get_object_or_404(Crop, pk=pk)
    return render(request, 'farm_app/crop_detail.html', {'crop': crop})


@login_required
def analyze_crop_view(request, pk):
   
    crop = get_object_or_404(Crop, pk=pk, user=request.user)

    if crop.user != request.user:
        messages.error(request, "Only the owner can analyze this crop.")
        return redirect('crop_detail', pk=pk)

    if not crop.s3_image_url:
        messages.error(request, 'No S3 image URL found for this crop.')
        return redirect('crop_detail', pk=pk)

    response = requests.get(crop.s3_image_url)
    if response.status_code != 200:
        messages.error(request, 'Failed to download image from S3.')
        return redirect('crop_detail', pk=pk)

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name

    analyzer = CropHealthAnalyzer()
    result = analyzer.analyze_image(tmp_path)

    if isinstance(result, dict):
        result_text = json.dumps(result, indent=2)
    else:
        result_text = str(result)

    crop.analyzed_result = result_text
    crop.status = 'analyzed'
    crop.analyzed_at = datetime.utcnow()
    crop.save()

    # Sending message to SQS
    message_dict = {
        "username": request.user.username,
        "user_email": request.user.email,
        "crop_id": crop.id,
        "crop_name": crop.name,
        "s3_image_url": crop.s3_image_url,
        "analysis_result": result,
        "analyzed_at": crop.analyzed_at.isoformat(),
    }
    send_analysis_message_to_sqs(message_dict)

    messages.success(request, 'Analysis completed locally. Lambda will update DynamoDB and send SNS notification.')
    return redirect('crop_detail', pk=pk)
