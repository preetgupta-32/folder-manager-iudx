from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('upload_page')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            
            # Auto-login after registration (optional)
            login(request, user)
            return redirect('upload_page')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserCreationForm()
    
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('upload_page')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_page = request.GET.get('next')
                if next_page and next_page != '/login/' and next_page != '/':
                    return redirect(next_page)
                return redirect('upload_page')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'auth/login.html', {'form': form})

@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def profile_view(request):
    """User profile view with file statistics"""
    user_folders = request.user.created_folders.all()
    user_files = request.user.uploaded_files.all()
    
    total_size = sum(f.file_size for f in user_files if f.file_size)
    
    context = {
        'user': request.user,
        'folder_count': user_folders.count(),
        'file_count': user_files.count(),
        'total_size': total_size,
        'recent_files': user_files.order_by('-uploaded_at')[:10],
        'is_admin': request.user.is_staff or request.user.is_superuser
    }
    
    return render(request, 'auth/profile.html', context)

@csrf_exempt
def api_login(request):
    """API endpoint for login (returns token)"""
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(username=username, password=password)
        if user:
            from rest_framework.authtoken.models import Token
            token, created = Token.objects.get_or_create(user=user)
            return JsonResponse({
                'status': 'success',
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'is_admin': user.is_staff or user.is_superuser
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid credentials'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def api_register(request):
    """API endpoint for registration"""
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        email = data.get('email', '')
        
        if not username or not password:
            return JsonResponse({'status': 'error', 'message': 'Username and password required'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'status': 'error', 'message': 'Username already exists'}, status=400)
        
        user = User.objects.create_user(username=username, password=password, email=email)
        
        from rest_framework.authtoken.models import Token
        token, created = Token.objects.get_or_create(user=user)
        
        return JsonResponse({
            'status': 'success',
            'token': token.key,
            'user_id': user.id,
            'username': user.username
        })
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)