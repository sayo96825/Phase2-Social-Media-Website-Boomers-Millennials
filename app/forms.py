from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Room 
from django.contrib.auth.models import User

# Form for User 
class UserCreationForm(UserCreationForm):
      class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

# Form for Room
class RoomForm(ModelForm):
    class Meta:
        model = Room
        fields = '__all__'
        exclude = ['host', 'participants']
        
# Form for Profile
class ProfileForm(ModelForm):
    class Meta:
        model =Profile
        fields = ['image', 'generation', 'skill', 'bio']