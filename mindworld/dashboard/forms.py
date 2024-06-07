from django import forms

class CreateServerForm(forms.Form):
    serverName = forms.CharField(max_length=100, label='Server Name')
    memory = forms.CharField(max_length=10, label='Memory Allocation', initial='2G')
    maxPlayers = forms.IntegerField(label='Max Players', initial=20)
    eula = forms.BooleanField(label='I agree to the Minecraft EULA')
