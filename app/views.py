import re
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User,auth
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from .models import Room, Topic, Message, Profile
from.forms import RoomForm, UserForm
#import requests

# Create your views here.

def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
#         email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            
            user = User.objects.filter(username=username).first()
        except:
            messages.error(request, 'User does not exist')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username OR password does not exit')

    context = {'page': page}
    return render(request, 'app/login_register.html', context)

def logoutUser(request):
    logout(request)
    return redirect('home')

def registerPage(request):
    page = "reister"
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Sorry, someting went wrong during registration ...')

    return render(request, 'app/login_register.html', {'form': form})

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q))
    topics = Topic.objects.all()
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))#[0:3]
    context = {'rooms': rooms,'topics': topics,'room_count': room_count, 'room_messages': room_messages}
    return render(request, 'app/home.html',context)

def room(request,pk):
    room = Room.objects.filter(id=pk).first()
    room_messages = room.message_set.all().order_by('-created')
    participants = room.participants.all()
    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)
    context = {'room': room, 'room_messages': room_messages,'participants': participants}
    return render(request, 'app/room.html',context)

def profile_list(request):
    
    profiles = Profile.objects.exclude(user=request.user)
    #profiles = Profile.objects.exclude(user=request.user)
    #folowed_by = profile.follows.exclude(user=request.user)
    #following
    # if request.method == "POST":
    #     current_user_profile = request.user.profile
    #     action = request.POST.get("action")
       
    #     print(action)
    #     if action == "follow":
    #         current_user_profile.follows.add(profile)
    #         print('follow-save')
            
    #     elif action == "unfollow":
    #         current_user_profile.follows.remove(profile)
    #         print('unfollow-save')
    #     current_user_profile.save()

    context = {"profiles":profiles}
    
    return render(request, 'app/profile_list.html', context)

def profile(request, pk):
    # if not hasattr(request.user, 'profile'):
    #     missing_profile = Profile(user=request.user)
        # missing_profile.save()
    user = User.objects.get(pk=pk)
    profile = Profile.objects.get(user=request.user)
    current_user = request.GET.get('user')
    #profile= Profile.objects.filter(pk=pk).first()
    #logged_in_user = request.user.username
    rooms = user.room_set.all()
    room_messages = profile.message_set.all()
    topics = Topic.objects.all()
    if request.method == "POST":
        current_user_profile = request.user.profile
        data = request.POST
        action = data.get("follow")
        if action == "follow":
            current_user_profile.follows.add(profile)
        elif action == "unfollow":
            current_user_profile.follows.remove(profile)
        current_user_profile.save()
    context = {"user":user,"profile":profile,"room_messages":room_messages,"rooms":rooms,"topics":topics}
    

    return render(request, "app/profile.html",context)


@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
#     topics = Topic.objects.all()
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.host = request.user
            room.save()
            return redirect('home')
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect('home')

    context =  {'form': form} #'topics': topic}
    return render(request, 'app/room_form.html', context)

@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.filter(id=pk).first()
    form = RoomForm(instance=room)
#     topics = Topic.objects.all()
    if request.user != room.host:
        return HttpResponse('Your need to be a host!!')

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('home')
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')

    context = {'form': form}#'topics': topics, 'room': room}
    return render(request, 'app/room_form.html', context)

@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.filter(id=pk).first()

    if request.user != room.host:
        return HttpResponse('Your need to be a host to delete this room!!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'app/delete.html', {'obj': room})

@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.filter(id=pk).first()

    if request.user != message.user:
        return HttpResponse('Your are not allowed here!!')

    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'app/delete.html', {'obj': message})

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    return render(request, 'app/update-user.html', {'form': form})

# def index(request):
#     pass

# def followers_count(request):
    
#     if request.method == 'POST':
#         value = request.POST['value']
#         user = request.POST['user']
#         follower = request.POST['follower']
#         if value == 'follow':
#             followers_cnt = FollowersCount.objects.create(follower=follower, user=user)
#             followers_cnt.save()
#         else:
#             followers_cnt = FollowersCount.objects.create(follower=follower, user=user)
#             followers_cnt.delete

#         return redirect('/?user='+user)
