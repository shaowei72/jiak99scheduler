from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def main_landing(request):
    """Main landing page for Jiak99 application."""
    return render(request, 'main_landing.html')
