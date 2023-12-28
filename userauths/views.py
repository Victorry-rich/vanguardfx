from django.shortcuts import render,redirect
from userauths.forms import UserRegisterForm
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import logout
from userauths.models import User
from django.conf import settings
from django.core.mail import send_mail, EmailMessage, EmailMultiAlternatives
import resend
import secrets
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Deposit
from django.db.models import Sum
def generate_reset_token():
    # Generate a URL-safe random token with 32 bytes (256 bits) of entropy
    return secrets.token_urlsafe(32)
def register_view(request):

    form = UserRegisterForm()
    if request.method == "POST":
        address = request.POST['address']
        username = request.POST['username']
        form = UserRegisterForm(request.POST or None)
        
        if form.is_valid():
            
            new_user = form.save()
            
            username = form.cleaned_data.get("username")
            email = form.cleaned_data.get('email')
            messages.success(request, f"Hey {username}, account created successfully")
            new_user = authenticate(username=form.cleaned_data['email'],
                                    password=form.cleaned_data['password1']
            )
            # send_activation_email(new_user,request)
            html_message = render_to_string('core/email.html')
            plain_message = strip_tags(html_message)
            login(request, new_user)
            

            # message = EmailMultiAlternatives(
            #     subject='Welcome to Vanguardfx',
            #     body= plain_message,
            #     from_email='support@Vanguardfx.net',
            #     to=[email]
            # )
            # message.attach_alternative(html_message,"text/html")
            # message.send()

            return redirect("core:dashboard")
    context = {
        'form': form,
    }
    return render(request, 'userauths/sign-up.html', context)

def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:index")
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Successfully logged in.")
                return redirect("core:dashboard")
            else:
                messages.warning(request, "Invalid credentials, create an account.")
        except:
            messages.warning(request, f"User does not exist")


    return render(request, 'userauths/sign-in.html' )





def get_user_data(request):
    # Retrieve the current user
    current_user = request.user

    # Fetch data for the current user
    data = {
        'total_balance': str(current_user.total_balance),
        'total_invested': str(current_user.total_invested),
        'total_deposit': str(current_user.total_deposit),
        # Add other fields as needed
    }

    return JsonResponse(data)

def get_total_deposit(request):
    # Retrieve the current user
    user = request.user
    confirmed_deposits = Deposit.objects.filter(user=user, confirmed=True)
    total_deposit = confirmed_deposits.aggregate(total_amount=Sum('amount'))['total_amount'] or 0

    # Fetch data for the current user
    data = {
        'total_deposit': str(total_deposit),
    }

    return JsonResponse(data)
def logout_view(request):
    logout(request)
    # messages.success(request, "User successfully logged out.")
    return redirect("core:index")

def lock_screen_view(request):
    logout(request)
    return redirect("userauths:sign-in")

def otp_view(request):
    return render(request, "userauths/otp.html")

def recover_password(request):
    return render(request,"userauths/recover_password.html")