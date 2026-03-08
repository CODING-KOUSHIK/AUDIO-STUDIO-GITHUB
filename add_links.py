import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import StudioLinkDatabase

PREDEFINED_MEETINGS = [
    {
        "Meeting ID": "meeting 0",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/016ca6ba-",
        "email2": "mohit.tripathi86@gmail.com"
    },
    {
        "Meeting ID": "meeting 1",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/8f55672b-",
        "email2": "aakash.srivastava97@gmail.com"
    },
    {
        "Meeting ID": "meeting 2",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/402a56b4-",
        "email2": "varun.rathore18@gmail.com"
    },
    {
        "Meeting ID": "meeting 3",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/9e518dc3-",
        "email2": "rajesh.soni29@gmail.com"
    },
    {
        "Meeting ID": "meeting 4",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/97f39789-",
        "email2": "tarun.chauhan30@gmail.com"
    },
    {
        "Meeting ID": "meeting 5",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/f947d99d-",
        "email2": "abhishek.joshi41@gmail.com"
    },
    {
        "Meeting ID": "meeting 6",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/07fbbc8a-",
        "email2": "pankaj.bansal52@gmail.com"
    },
    {
        "Meeting ID": "meeting 7",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/a954d904-",
        "email2": "alok.saini63@gmail.com"
    },
    {
        "Meeting ID": "meeting 8",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/9a4c9c8c-",
        "email2": "gaurav.bhardwaj74@gmail.com"
    },
    {
        "Meeting ID": "meeting 9",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/b060aefe-",
        "email2": "yogesh.solanki85@gmail.com"
    },
    {
        "Meeting ID": "meeting 10",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/bcdb27bf-",
        "email2": "harsh.vashisht96@gmail.com"
    },
    {
        "Meeting ID": "meeting 11",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/0367dfd8-",
        "email2": "naveen.rana17@gmail.com"
    },
    {
        "Meeting ID": "meeting 12",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/ba85defc-",
        "email2": "vikas.khatri28@gmail.com"
    },
    {
        "Meeting ID": "meeting 13",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/1ff03dae-",
        "email2": "sachin.lodhi39@gmail.com"
    },
    {
        "Meeting ID": "meeting 14",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/e8d40a5a-",
        "email2": "pradeep.kohli40@gmail.com"
    },
    {
        "Meeting ID": "meeting 15",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/4bdad7fb-",
        "email2": "swati.sharma51@gmail.com"
    },
    {
        "Meeting ID": "meeting 16",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/7d52d018-",
        "email2": "komal.verma62@gmail.com"
    },
    {
        "Meeting ID": "meeting 17",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/1daa0f7b-",
        "email2": "tanya.gupta73@gmail.com"
    },
    {
        "Meeting ID": "meeting 18",
        "email1": "amit.sharma12@gmail.com",
        "meeting_url": "https://prod-audio-studio.kgen.io/studio/ba2d900a-",
        "email2": "sonal.patel84@gmail.com"
    }
]

StudioLinkDatabase.objects.all().delete()

for link in PREDEFINED_MEETINGS:
    StudioLinkDatabase.objects.create(
        name_id=link['Meeting ID'],
        email1=link['email1'],
        email2=link['email2'],
        meeting_url=link['meeting_url'],
        is_used=False
    )
    
print(f"Successfully added {len(PREDEFINED_MEETINGS)} studio links to the database.")
