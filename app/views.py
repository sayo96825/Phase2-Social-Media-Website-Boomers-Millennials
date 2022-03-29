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
from.forms import RoomForm, ProfileForm 

# Create your views here.

#log in function for existing user
def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
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

# logout function
def logoutUser(request):
    logout(request)
    return redirect('home')

# register function for new user
def registerPage(request):
    page = "register"
    # form for new user creation
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            Profile.objects.create(
                user=user
            )   
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Sorry, someting went wrong during registration ...')
    return render(request, 'app/login_register.html', {'form': form})

#Homepage function
def home(request):
    # User can search topic 
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(Q(topic__name__icontains=q) |
                                Q(name__icontains=q) |
                                Q(description__icontains=q))
    topics = Topic.objects.all()
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))
    context = {'rooms': rooms,'topics': topics,'room_count': room_count, 'room_messages': room_messages}
    return render(request, 'app/home.html',context)

#create room function
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

# User profile function
def userProfile(request, pk):
    current_user = request.GET.get('user')
    user = Profile.objects.filter(id=pk).first()
    profile= Profile.objects.filter(id=pk).first()
    topics = Topic.objects.all()
    profile2 = Profile.objects.exclude(user=request.user)
    image = request.POST.get('image')
    # User can follow and unfollow other users
    if request.method == "POST":
        current_user_profile = request.user.profile
        action = request.POST.get("action")     
        print(action)
        if action == "follow":
            current_user_profile.follows.add(profile)
            print('follow-save')         
        elif action == "unfollow":
            current_user_profile.follows.remove(profile)
            print('unfollow-save')
        current_user_profile.save()
    context = {'user': user,'current_user':current_user, 'topics': topics,"profiles":profile,"profile2": profile2}
    return render(request, 'app/profile_list.html', context)

# User lists function
def profile(request):
    user= Profile.objects.filter(user=request.user).first()
    profile = Profile.objects.exclude(user=request.user)
    return render(request, "app/profile.html", {"profile3": profile,'user':user})

# If use is log in, user can create a room
@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.host = request.user
            room.save()
            return redirect('home')
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        # creating room objects
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect('home')
    context =  {'form': form,'topics': topics}
    return render(request, 'app/room_form.html', context)

# Function to update the existing room
@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.filter(id=pk).first()
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    if request.user != room.host:
        return HttpResponse('Your need to be a host!!')
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('home')
        topic_name = request.POST.get('topic')
        # user can add their own topic and choose from the existing topics
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')
    context = {'form': form,'topics': topics, 'room': room}
    return render(request, 'app/room_form.html', context)

# Room host can delete the room
@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.filter(id=pk).first()
    if request.user != room.host:
        return HttpResponse('Your need to be a host to delete this room!!')
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'app/delete.html', {'obj': room})

# User can delete their own message
@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.filter(id=pk).first()
    if request.user != message.user:
        return HttpResponse('Your are not allowed here!!')
    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'app/delete.html', {'obj': message})

# This function let user to update their own profile
# User can add prfofie picture, their generation, bio and skills
@login_required(login_url='login')
def updateUser(request):
    user = request.user.profile
    form = ProfileForm(instance=user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
        Profile.objects.create(
            bio = request.POST.get('bio'),
            generation = request.POST.get('generation'),
            image = request.POST.get('image'),
            skill = request.POST.get('skill'),
        )
        return redirect('user-profile', pk=user.id)
    context ={'form': form } 
    return render(request, 'app/update-user.html', context)