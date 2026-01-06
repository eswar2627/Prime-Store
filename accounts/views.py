from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from orders.models import Order
from .models import Address
from .forms import AddressForm
from django.contrib import messages
from django.http import JsonResponse
@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/address_list.html', {'addresses': addresses})
@login_required
def address_add(request):
    if request.method == "POST":
        Address.objects.create(
            user=request.user,
            full_name=request.POST["full_name"],
            phone=request.POST["phone"],
            city=request.POST["city"],
            state=request.POST["state"],
            postal_code=request.POST["postal_code"],
        )
        return JsonResponse({"success": True})
    form = AddressForm()
    return render(request, "accounts/address_form.html", {"form": form})

@login_required
def address_edit(request, id):
    address = Address.objects.get(id=id, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            addr = form.save(commit=False)
            if addr.is_default:
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            addr.save()
            messages.success(request, "Address updated successfully!")
            return redirect('accounts:address_list')
    else:
        form = AddressForm(instance=address)
    return render(request, 'accounts/address_form.html', {'form': form})
@login_required
def address_delete(request, id):
    address = Address.objects.get(id=id, user=request.user)
    address.delete()
    messages.success(request, "Address deleted successfully!")
    return redirect('accounts:address_list')
@login_required
def address_set_default(request, id):
    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
    selected = Address.objects.get(id=id, user=request.user)
    selected.is_default = True
    selected.save()
    messages.success(request, "Default address updated!")
    return redirect('accounts:address_list')
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('accounts:login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect('store:product_list')
        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid username or password'})
    return render(request, 'accounts/login.html')
def logout_view(request):
    logout(request)
    return redirect('store:product_list')
@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')
@login_required
def order_history(request):
    orders = Order.objects.filter(email=request.user.email)
    return render(request, 'accounts/order_history.html', {'orders': orders})