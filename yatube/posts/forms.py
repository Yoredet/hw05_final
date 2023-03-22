from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image', )
        required = ('text',)

    def clean_text(self):
        data = self.cleaned_data['text']
        if not data:
            raise forms.ValidationError('Поле должно быть заполнено')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )
        required = ('text', )
