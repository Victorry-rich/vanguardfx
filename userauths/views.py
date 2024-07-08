from django.shortcuts import render,redirect
from userauths.forms import UserRegisterForm
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth import logout
from userauths.models import User
import resend
from django.http import JsonResponse
from .models import Deposit
from django.db.models import Sum
from userauths.models import Transaction
from django.utils import timezone
from .models import UserToken
from .utils import send_confirmation_email, reset_password
from django.contrib.auth.hashers import make_password
from django.db import transaction as ts
from django.conf import settings
resend.api_key = getattr(settings, 'SENSITIVE_VARIABLE', None)

def perform_daily_task():
    try:
        current_time = timezone.now()

        # Fetch only the transactions that are not processed yet
        transactions = Transaction.objects.filter(plan_interval_processed=False, confirmed=True)

        for transaction in transactions:
            time_difference = current_time - transaction.timestamp
            if int(transaction.interval_count) < int(transaction.convert_description_to_days()) and (time_difference.days >= transaction.days_count):
               
                 
                    amount_to_add = transaction.percentage_return * transaction.amount / 100
                
                    # Update the user's total_invested field
                    transaction.user.total_invested += amount_to_add
                    transaction.user.save()
 
                    # Update interval_count and days_count
                    transaction.interval_count += 1
                    transaction.days_count += 1

                    # Save all changes at once
                    transaction.save(update_fields=['interval_count', 'days_count'])

            # elif transaction.interval_count >= 7:
                
            #     # Move total_invested to total_deposit
            #     transaction.user.total_deposit += transaction.user.total_invested
            #     transaction.user.total_invested = 0
            #     transaction.user.save(update_fields=['total_deposit', 'total_invested'])

            #     # Set plan_interval_processed to True
            #     transaction.plan_interval_processed = True
            #     transaction.save()

            elif time_difference.days >= int(transaction.convert_description_to_days()):
                 # Move total_invested to total_deposit
                transaction.user.total_deposit += transaction.user.total_invested
                transaction.user.total_invested = 0
                transaction.user.save(update_fields=['total_deposit', 'total_invested'])

                # Set plan_interval_processed to True
                transaction.plan_interval_processed = True
                transaction.save()
            else: 
                pass



    except Exception as e:
        print(f"Error in perform_daily_task: {e}")



def register_view(request):
    pre_filled_email = request.session.get('pre_filled_email', '')
    form = UserRegisterForm(initial={'email': pre_filled_email})
    if request.method == "POST":
        address = request.POST['address']
        username = request.POST['username']
        form = UserRegisterForm(request.POST or None)
        
        if form.is_valid():
            
            new_user = form.save(commit=False)  # Don't save the user yet
            new_user.email_verified = False
            new_user.save()
            send_confirmation_email(request, new_user)
            
            username = form.cleaned_data.get("username")
            email = form.cleaned_data.get('email')
            messages.success(request, f"Hey {username}, an email a confirmation email has been sent")

            new_user = authenticate(username=form.cleaned_data['email'],
                                    password=form.cleaned_data['password1']
            )
         
          
            try:
                r = resend.Emails.send({
                    "from": "Cryptovest <support@cryptovest.online>",
                    "to": 'philipebenezer74@gmail.com',
                    "subject": "New User",
                    "html": f"""
                        <!DOCTYPE html>
                        <html lang="en">
                        
                        <body>
                            <div class="container">
                                <h1>Hey Admin,<br> Someone created an account !</h1>
                                <p>A new user with the name {username} and email {email} signed up to Cryptovest.</p>
                                <p>Check them out, they can be potential clients</p>
                                <p>Login to your admin panel to view them:</p><br><br>
                                <div style="text-align: center; align-items: center;">
                                    <a href="https://cryptovest.online/admin/userauths/user/" class="btn btn-primary" style="background-color: #007bff; font-size: 16px; border-color: #007bff; padding: 10px 20px; border-radius: 2px;" target="_blank">Admin Panel</a><br><br>
                                </div>
                                
                            </div>
                        </body>
                        </html>
                    """,
                })
    
            except Exception as e:
                pass

   

            return redirect("core:dashboard")
    context = {
        'form': form,
        
    }
    return render(request, 'userauths/sign-up.html', context)

def referral_signup(request):
    ref = request.GET.get('ref')
    form = UserRegisterForm()
    if request.method == "POST":
        username = request.POST['username']
        form = UserRegisterForm(request.POST or None)
        
        if form.is_valid():
            
            new_user = form.save(commit=False)  # Don't save the user yet
            new_user.email_verified = False
            new_user.save()
            send_confirmation_email(request, new_user)
            
            username = form.cleaned_data.get("username")
            email = form.cleaned_data.get('email')
            messages.success(request, f"Hey {username}, an email a confirmation email has been sent")
            new_user = authenticate(username=form.cleaned_data['email'],
                                    password=form.cleaned_data['password1']
            )
            try:
                r = resend.Emails.send({
                    "from": "Cryptovest <support@cryptovest.online>",
                    "to": 'hello@cryptovest.online',
                    "subject": "New User",
                    "html": f"""
                        <!DOCTYPE html>
                        <html lang="en">
                    
                        <body>
                            <div class="container">
                                <h1>Hey Admin,<br> Someone created an account !</h1>
                                <p>A new user with the name {username} and email {email} signed up to Cryptovest.</p>
                                <p>Check them out, they can be potential clients</p>
                                <p>Login to your admin panel to view them:</p><br><br>
                                <div style="text-align: center; align-items: center;">
                                    <a href="https://cryptovest.online/admin/userauths/user/" class="btn btn-primary" style="background-color: #007bff; color: #fff; font-size: 16px; border-color: #007bff; padding: 10px 20px; border-radius: 2px;" target="_blank">Admin Panel</a><br><br>
                                </div>
                                
                            </div>

                        
                        </body>
                        </html>
                    """,
                })
            except Exception as e:
                pass
  
            

   

            return redirect("core:dashboard")
        
    if ref:
        form.fields['referred'].initial = ref
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
                perform_daily_task()
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
    if current_user.is_authenticated:
        data = {
            'total_invested': str(current_user.total_invested),
            'total_deposit': str(current_user.total_deposit),
            # Add other fields as needed
        }
        return JsonResponse(data)


def get_total_deposit(request):
    # Retrieve the current user
    user = request.user
    confirmed_deposits = Deposit.objects.filter(user=user, confirmed=True)
    valid_transactiions = Transaction.objects.filter(user=user)
    total_transactions = valid_transactiions.aggregate(total_amount=Sum('amount'))['total_amount'] or 0
    total_deposits = confirmed_deposits.aggregate(total_amount=Sum('amount'))['total_amount'] or 0

    # Fetch data for the current user
    if user.is_authenticated:
        data = {
            'total_deposits': str(total_deposits),
            'total_transactions': str(total_transactions),
        }
        return JsonResponse(data)
def logout_view(request):
    logout(request)
    # messages.success(request, "User successfully logged out.")
    return redirect("core:index")

def lock_screen_view(request):
    logout(request)
    return redirect("userauths:sign-in")


def forgot_password(request):
    return render(request, "userauths/forgot-password.html")


            
            


def trigger_daily_task(request):
    # Call your perform_daily_task function here

    perform_daily_task()

    # Return a JSON response indicating success
    return JsonResponse({'status': 'success'})


def send_password_reset(request):
    if request.method == 'POST' and request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        try:
            if user:
                reset_password(request, user)
                return JsonResponse({'success': True, 'message': "A password reset email has been sent to your email"})
            else:
                return JsonResponse({'success': False, 'message': "User with this email does not exist."})
        except Exception as e:
            print(e)
    else:
        return JsonResponse({'success': False, 'message': "Invalid request"})

def password_reset_form(request, token):
    try:
        user_token = UserToken.objects.get(token=token, token_type='password_reset', used=False)
    except UserToken.DoesNotExist:
            # Token not found or already used
            return redirect('userauths:invalid_token')
    return render(request, 'password/password_reset_form.html', {'token': token})

def process_password_reset(request):
    if request.method == 'POST':
        token = request.POST.get('token')
        password = request.POST.get('password')
        
        try:
            user_token = UserToken.objects.get(token=token, token_type='password_reset', used=False)
        except UserToken.DoesNotExist:
            # Token not found or already used
            return redirect('userauths:invalid_token')
        
        # Check if the token has expired
        if user_token.expires_at < timezone.now():
            # Token has expired
            return redirect('userauths:invalid_token')
        
        # Mark the token as used
        user_token.used = True
        user_token.save()
        
        # Update the user's password
        user = user_token.user
        user.password = make_password(password)
        user.save()
        user_token.delete()
        
        return redirect('userauths:password-reset-success')  # Redirect to a page indicating that the password has been reset
    
    return redirect('home')  # Redirect to home page if the request method is not POST


def email_invalid(request):
    return render(request, "emails/email-invalid.html")

def password_reset_success(request):
    return render(request, "password/password-reset-success.html")


def email_confirmed(request):
    return render(request, "emails/email-confirmed.html")