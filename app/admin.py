from django.contrib import admin

# Register your models here.

from .models import Room, Topic, Message, Profile,User

admin.site.register(Room)
admin.site.register(Topic)
admin.site.register(Message)
admin.site.register(Profile)

class ProfileInline(admin.StackedInline):
    model = Profile

class UserAdmin(admin.ModelAdmin):
    model = User
    fields = ["username","email"]
    inlines = [ProfileInline]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)