from django.contrib import admin
from django.contrib.auth.models import User
# Register your models here.

from .models import Room, Topic, Message, Profile

admin.site.register(Room)
admin.site.register(Topic)
admin.site.register(Message)

class ProfileInline(admin.StackedInline):
    model = Profile

class UserAdmin(admin.ModelAdmin):
    model = User
    fields = ["username","email"]
    inlines = [ProfileInline]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)