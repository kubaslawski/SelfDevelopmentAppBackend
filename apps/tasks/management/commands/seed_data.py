"""
Management command to seed the database with sample users and tasks.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.tasks.models import Task, TaskCompletion

User = get_user_model()


class Command(BaseCommand):
    help = "Seed database with 10 users, each with 10 unique tasks"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing data before seeding",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            TaskCompletion.objects.all().delete()
            Task.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS("Data cleared!"))

        self.stdout.write("Seeding users and tasks...")

        # Each user has a different focus area with unique tasks
        users_with_tasks = [
            # User 1: Fitness Enthusiast
            {
                "user": {
                    "username": "john_doe",
                    "email": "john@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                },
                "tasks": [
                    {
                        "title": "Morning stretching routine",
                        "description": "Start each day with 10 minutes of stretching to improve flexibility.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 10,
                        "tags": "fitness, morning, flexibility",
                    },
                    {
                        "title": "Track daily calories intake",
                        "description": "Log all meals in MyFitnessPal to maintain awareness of nutrition.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 5,
                        "tags": "nutrition, tracking, health",
                    },
                    {
                        "title": "Drink protein shake after workout",
                        "description": "Consume 30g protein within 30 minutes post-exercise for muscle recovery.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 4,
                        "duration": 5,
                        "tags": "nutrition, protein, recovery",
                    },
                    {
                        "title": "Complete strength training session",
                        "description": "Full body workout focusing on compound movements: squats, deadlifts, bench press.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 3,
                        "duration": 60,
                        "tags": "strength, gym, workout",
                    },
                    {
                        "title": "Run 5K without stopping",
                        "description": "Build cardiovascular endurance by running 5 kilometers continuously.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 2,
                        "duration": 30,
                        "tags": "running, cardio, endurance",
                    },
                    {
                        "title": "Try a new healthy recipe",
                        "description": "Experiment with nutritious cooking - focus on high protein, low processed foods.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 1,
                        "duration": 45,
                        "tags": "cooking, nutrition, health",
                    },
                    {
                        "title": "Achieve 10,000 steps daily",
                        "description": "Stay active throughout the day by walking more and taking stairs.",
                        "priority": "high",
                        "period": "daily",
                        "target": 1,
                        "duration": 60,
                        "tags": "walking, activity, health",
                    },
                    {
                        "title": "Master a new exercise form",
                        "description": "Learn proper technique for Olympic lifts or advanced calisthenics moves.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 2,
                        "duration": 30,
                        "tags": "technique, learning, fitness",
                    },
                    {
                        "title": "Complete a fitness challenge",
                        "description": "30-day challenge: 100 pushups, 100 squats, 100 situps daily.",
                        "priority": "urgent",
                        "period": "daily",
                        "target": 1,
                        "duration": 45,
                        "tags": "challenge, discipline, strength",
                    },
                    {
                        "title": "Train for half-marathon",
                        "description": "Follow a structured 12-week training plan to run 21.1km.",
                        "priority": "urgent",
                        "period": "weekly",
                        "target": 4,
                        "duration": 90,
                        "tags": "marathon, running, ambitious",
                    },
                ],
            },
            # User 2: Tech Professional
            {
                "user": {
                    "username": "jane_smith",
                    "email": "jane@example.com",
                    "first_name": "Jane",
                    "last_name": "Smith",
                },
                "tasks": [
                    {
                        "title": "Review tech news and updates",
                        "description": "Spend 10 minutes reading Hacker News or TechCrunch to stay informed.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 10,
                        "tags": "tech, news, learning",
                    },
                    {
                        "title": "Practice typing speed",
                        "description": "Use keybr.com or typing.com to improve typing to 80+ WPM.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 10,
                        "tags": "typing, productivity, skill",
                    },
                    {
                        "title": "Solve one coding challenge",
                        "description": "Complete a LeetCode or HackerRank problem to sharpen algorithms.",
                        "priority": "medium",
                        "period": "daily",
                        "target": 1,
                        "duration": 30,
                        "tags": "coding, algorithms, practice",
                    },
                    {
                        "title": "Contribute to open source",
                        "description": "Submit a PR or fix a bug in an open source project on GitHub.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 1,
                        "duration": 60,
                        "tags": "opensource, github, community",
                    },
                    {
                        "title": "Learn a new programming concept",
                        "description": "Study design patterns, system design, or new language features.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 2,
                        "duration": 45,
                        "tags": "learning, programming, concepts",
                    },
                    {
                        "title": "Build a personal project feature",
                        "description": "Add functionality to your portfolio project or side hustle app.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 3,
                        "duration": 90,
                        "tags": "project, coding, portfolio",
                    },
                    {
                        "title": "Write a technical blog post",
                        "description": "Share knowledge by writing about a problem you solved or technology you learned.",
                        "priority": "high",
                        "period": "monthly",
                        "target": 2,
                        "duration": 120,
                        "tags": "writing, blog, teaching",
                    },
                    {
                        "title": "Complete AWS certification module",
                        "description": "Study for AWS Solutions Architect or similar cloud certification.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 3,
                        "duration": 60,
                        "tags": "aws, certification, cloud",
                    },
                    {
                        "title": "Mentor a junior developer",
                        "description": "Schedule pair programming or code review sessions with less experienced colleagues.",
                        "priority": "urgent",
                        "period": "weekly",
                        "target": 1,
                        "duration": 60,
                        "tags": "mentoring, leadership, teaching",
                    },
                    {
                        "title": "Build and deploy a SaaS product",
                        "description": "Create a complete product from idea to production with paying customers.",
                        "priority": "urgent",
                        "period": "weekly",
                        "target": 5,
                        "duration": 120,
                        "tags": "saas, entrepreneurship, ambitious",
                    },
                ],
            },
            # User 3: Language Learner
            {
                "user": {
                    "username": "mike_wilson",
                    "email": "mike@example.com",
                    "first_name": "Mike",
                    "last_name": "Wilson",
                },
                "tasks": [
                    {
                        "title": "Review flashcards on Anki",
                        "description": "Spend 10 minutes reviewing vocabulary flashcards using spaced repetition.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 10,
                        "tags": "vocabulary, anki, memory",
                    },
                    {
                        "title": "Listen to a podcast in target language",
                        "description": "Immerse yourself by listening to native content during commute or exercise.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 20,
                        "tags": "listening, podcast, immersion",
                    },
                    {
                        "title": "Complete Duolingo daily goal",
                        "description": "Maintain your streak by completing at least one lesson.",
                        "priority": "medium",
                        "period": "daily",
                        "target": 1,
                        "duration": 15,
                        "tags": "duolingo, practice, streak",
                    },
                    {
                        "title": "Watch a movie without subtitles",
                        "description": "Challenge your comprehension by watching foreign films without English subtitles.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 1,
                        "duration": 120,
                        "tags": "movies, listening, comprehension",
                    },
                    {
                        "title": "Practice speaking with language partner",
                        "description": "Use iTalki or Tandem to have a 30-minute conversation with a native speaker.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 2,
                        "duration": 30,
                        "tags": "speaking, conversation, practice",
                    },
                    {
                        "title": "Read a book chapter in target language",
                        "description": "Improve reading comprehension by tackling native literature.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 3,
                        "duration": 45,
                        "tags": "reading, books, comprehension",
                    },
                    {
                        "title": "Write a journal entry in target language",
                        "description": "Practice writing by describing your day or thoughts in the language you're learning.",
                        "priority": "high",
                        "period": "daily",
                        "target": 1,
                        "duration": 15,
                        "tags": "writing, journal, practice",
                    },
                    {
                        "title": "Learn 20 new vocabulary words",
                        "description": "Expand your vocabulary systematically with context and example sentences.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 1,
                        "duration": 30,
                        "tags": "vocabulary, learning, words",
                    },
                    {
                        "title": "Take an online language class",
                        "description": "Enroll in structured lessons with a professional teacher for grammar and conversation.",
                        "priority": "urgent",
                        "period": "weekly",
                        "target": 2,
                        "duration": 60,
                        "tags": "class, teacher, structured",
                    },
                    {
                        "title": "Achieve B2 certification level",
                        "description": "Prepare for and pass an official language proficiency exam (DELF, JLPT, HSK, etc.).",
                        "priority": "urgent",
                        "period": "weekly",
                        "target": 5,
                        "duration": 90,
                        "tags": "certification, exam, fluency",
                    },
                ],
            },
            # User 4: Mindfulness & Mental Health
            {
                "user": {
                    "username": "sarah_jones",
                    "email": "sarah@example.com",
                    "first_name": "Sarah",
                    "last_name": "Jones",
                },
                "tasks": [
                    {
                        "title": "Practice deep breathing exercises",
                        "description": "Take 5 minutes for box breathing or 4-7-8 technique to reduce stress.",
                        "priority": "low",
                        "period": "daily",
                        "target": 2,
                        "duration": 5,
                        "tags": "breathing, relaxation, stress",
                    },
                    {
                        "title": "Write three gratitude items",
                        "description": "Before bed, write down three things you're grateful for today.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 5,
                        "tags": "gratitude, journaling, positivity",
                    },
                    {
                        "title": "Morning meditation session",
                        "description": "Start the day with guided meditation using Headspace or Calm app.",
                        "priority": "medium",
                        "period": "daily",
                        "target": 1,
                        "duration": 15,
                        "tags": "meditation, morning, mindfulness",
                    },
                    {
                        "title": "Digital detox hour",
                        "description": "Spend one hour without any screens - read, walk, or simply be present.",
                        "priority": "medium",
                        "period": "daily",
                        "target": 1,
                        "duration": 60,
                        "tags": "detox, screens, presence",
                    },
                    {
                        "title": "Practice yoga or tai chi",
                        "description": "Combine physical movement with mindfulness through gentle exercise.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 3,
                        "duration": 45,
                        "tags": "yoga, movement, mindfulness",
                    },
                    {
                        "title": "Journal about emotions and thoughts",
                        "description": "Free-write about your feelings to process and understand them better.",
                        "priority": "high",
                        "period": "daily",
                        "target": 1,
                        "duration": 20,
                        "tags": "journaling, emotions, reflection",
                    },
                    {
                        "title": "Spend quality time in nature",
                        "description": "Go for a mindful walk in a park, forest, or near water.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 2,
                        "duration": 60,
                        "tags": "nature, walking, peace",
                    },
                    {
                        "title": "Read a self-help or psychology book",
                        "description": "Learn about mental health, habits, or personal growth from experts.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 1,
                        "duration": 30,
                        "tags": "reading, psychology, growth",
                    },
                    {
                        "title": "Attend a therapy or coaching session",
                        "description": "Work with a professional to address challenges and set goals.",
                        "priority": "urgent",
                        "period": "weekly",
                        "target": 1,
                        "duration": 60,
                        "tags": "therapy, coaching, professional",
                    },
                    {
                        "title": "Complete a 30-day meditation challenge",
                        "description": "Build a solid meditation practice by committing to 30 consecutive days.",
                        "priority": "urgent",
                        "period": "daily",
                        "target": 1,
                        "duration": 20,
                        "tags": "challenge, meditation, habit",
                    },
                ],
            },
            # User 5: Creative Artist
            {
                "user": {
                    "username": "david_brown",
                    "email": "david@example.com",
                    "first_name": "David",
                    "last_name": "Brown",
                },
                "tasks": [
                    {
                        "title": "Daily sketch practice",
                        "description": "Draw anything for 15 minutes - people, objects, or abstract shapes.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 15,
                        "tags": "drawing, sketch, practice",
                    },
                    {
                        "title": "Explore a new art technique",
                        "description": "Watch a tutorial and try watercolors, charcoal, or digital art.",
                        "priority": "low",
                        "period": "weekly",
                        "target": 1,
                        "duration": 30,
                        "tags": "technique, learning, experimentation",
                    },
                    {
                        "title": "Take reference photos",
                        "description": "Photograph interesting subjects, textures, and compositions for future artwork.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 2,
                        "duration": 30,
                        "tags": "photography, reference, inspiration",
                    },
                    {
                        "title": "Study art from masters",
                        "description": "Analyze works by famous artists - understand composition, color, and technique.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 1,
                        "duration": 45,
                        "tags": "study, masters, analysis",
                    },
                    {
                        "title": "Work on a larger art piece",
                        "description": "Dedicate focused time to a more ambitious artwork that takes multiple sessions.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 3,
                        "duration": 90,
                        "tags": "artwork, project, creation",
                    },
                    {
                        "title": "Share art on social media",
                        "description": "Post your work on Instagram or ArtStation to build an audience and get feedback.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 2,
                        "duration": 15,
                        "tags": "social, sharing, community",
                    },
                    {
                        "title": "Participate in an art challenge",
                        "description": "Join Inktober, Draw This In Your Style, or similar community challenges.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 3,
                        "duration": 60,
                        "tags": "challenge, community, practice",
                    },
                    {
                        "title": "Create art for a client or commission",
                        "description": "Take on paid work to build portfolio and earn from your skills.",
                        "priority": "high",
                        "period": "monthly",
                        "target": 1,
                        "duration": 180,
                        "tags": "commission, client, professional",
                    },
                    {
                        "title": "Attend a life drawing session",
                        "description": "Practice figure drawing with live models to improve human anatomy skills.",
                        "priority": "urgent",
                        "period": "weekly",
                        "target": 1,
                        "duration": 120,
                        "tags": "figure, anatomy, live",
                    },
                    {
                        "title": "Prepare portfolio for gallery submission",
                        "description": "Curate your best work for exhibition opportunities or art school applications.",
                        "priority": "urgent",
                        "period": "weekly",
                        "target": 2,
                        "duration": 60,
                        "tags": "portfolio, gallery, ambitious",
                    },
                ],
            },
            # User 6: Financial Growth
            {
                "user": {
                    "username": "emily_davis",
                    "email": "emily@example.com",
                    "first_name": "Emily",
                    "last_name": "Davis",
                },
                "tasks": [
                    {
                        "title": "Track daily expenses",
                        "description": "Log every purchase in a budgeting app like YNAB or Mint.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 5,
                        "tags": "budget, tracking, expenses",
                    },
                    {
                        "title": "Review financial news",
                        "description": "Stay informed about markets and economy with Bloomberg or WSJ.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 10,
                        "tags": "news, markets, finance",
                    },
                    {
                        "title": "Transfer to savings account",
                        "description": "Automate weekly savings by moving money to a high-yield savings account.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 1,
                        "duration": 5,
                        "tags": "savings, automation, wealth",
                    },
                    {
                        "title": "Review and categorize spending",
                        "description": "Analyze where your money goes and identify areas to cut back.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 1,
                        "duration": 30,
                        "tags": "budget, analysis, spending",
                    },
                    {
                        "title": "Research investment opportunities",
                        "description": "Study stocks, ETFs, or real estate options for growing wealth.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 2,
                        "duration": 45,
                        "tags": "investing, research, stocks",
                    },
                    {
                        "title": "Read a personal finance book",
                        "description": "Learn from experts like Ramit Sethi, Dave Ramsey, or Morgan Housel.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 1,
                        "duration": 30,
                        "tags": "reading, finance, education",
                    },
                    {
                        "title": "Rebalance investment portfolio",
                        "description": "Review asset allocation and adjust to maintain your target risk level.",
                        "priority": "high",
                        "period": "monthly",
                        "target": 1,
                        "duration": 60,
                        "tags": "portfolio, investing, rebalance",
                    },
                    {
                        "title": "Negotiate a bill or subscription",
                        "description": "Call service providers to reduce rates or cancel unused subscriptions.",
                        "priority": "high",
                        "period": "monthly",
                        "target": 2,
                        "duration": 30,
                        "tags": "negotiation, savings, bills",
                    },
                    {
                        "title": "Create additional income stream",
                        "description": "Start a side hustle, freelancing, or passive income project.",
                        "priority": "urgent",
                        "period": "weekly",
                        "target": 3,
                        "duration": 120,
                        "tags": "income, side-hustle, entrepreneurship",
                    },
                    {
                        "title": "Plan for financial independence",
                        "description": "Calculate FIRE number and create a long-term wealth building strategy.",
                        "priority": "urgent",
                        "period": "weekly",
                        "target": 2,
                        "duration": 60,
                        "tags": "fire, independence, planning",
                    },
                ],
            },
            # User 7: Career Professional
            {
                "user": {
                    "username": "chris_miller",
                    "email": "chris@example.com",
                    "first_name": "Chris",
                    "last_name": "Miller",
                },
                "tasks": [
                    {
                        "title": "Organize inbox and respond to emails",
                        "description": "Achieve inbox zero by processing and responding to all important emails.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 20,
                        "tags": "email, organization, productivity",
                    },
                    {
                        "title": "Plan tomorrow's priorities",
                        "description": "End each workday by listing top 3 tasks for the next day.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 10,
                        "tags": "planning, priorities, productivity",
                    },
                    {
                        "title": "Update LinkedIn profile",
                        "description": "Keep your professional profile current with recent achievements and skills.",
                        "priority": "medium",
                        "period": "monthly",
                        "target": 1,
                        "duration": 30,
                        "tags": "linkedin, profile, networking",
                    },
                    {
                        "title": "Connect with a colleague",
                        "description": "Build relationships by having coffee or a virtual chat with coworkers.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 2,
                        "duration": 30,
                        "tags": "networking, relationships, colleagues",
                    },
                    {
                        "title": "Attend industry webinar or event",
                        "description": "Stay current by participating in professional development events.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 1,
                        "duration": 60,
                        "tags": "webinar, industry, learning",
                    },
                    {
                        "title": "Document accomplishments for review",
                        "description": "Keep a brag document of your wins and contributions.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 1,
                        "duration": 15,
                        "tags": "accomplishments, review, career",
                    },
                    {
                        "title": "Practice public speaking",
                        "description": "Join Toastmasters or practice presentations to improve communication.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 1,
                        "duration": 60,
                        "tags": "speaking, presentation, communication",
                    },
                    {
                        "title": "Seek feedback from manager",
                        "description": "Schedule regular 1:1s to discuss performance and growth areas.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 1,
                        "duration": 30,
                        "tags": "feedback, manager, growth",
                    },
                    {
                        "title": "Apply for stretch assignments",
                        "description": "Volunteer for challenging projects that expand your skills and visibility.",
                        "priority": "urgent",
                        "period": "monthly",
                        "target": 1,
                        "duration": 60,
                        "tags": "growth, projects, visibility",
                    },
                    {
                        "title": "Prepare for promotion conversation",
                        "description": "Build your case with evidence and schedule a career discussion with leadership.",
                        "priority": "urgent",
                        "period": "weekly",
                        "target": 2,
                        "duration": 60,
                        "tags": "promotion, career, ambitious",
                    },
                ],
            },
            # User 8: Music & Performing Arts
            {
                "user": {
                    "username": "amanda_taylor",
                    "email": "amanda@example.com",
                    "first_name": "Amanda",
                    "last_name": "Taylor",
                },
                "tasks": [
                    {
                        "title": "Warm up voice or instrument",
                        "description": "Start practice with scales, arpeggios, or vocal exercises.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 15,
                        "tags": "warmup, practice, technique",
                    },
                    {
                        "title": "Listen to new music for inspiration",
                        "description": "Discover new artists and genres to expand your musical horizons.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 20,
                        "tags": "listening, inspiration, discovery",
                    },
                    {
                        "title": "Practice current repertoire",
                        "description": "Work on pieces you're learning with focus on difficult passages.",
                        "priority": "medium",
                        "period": "daily",
                        "target": 1,
                        "duration": 45,
                        "tags": "practice, repertoire, improvement",
                    },
                    {
                        "title": "Learn a new song or piece",
                        "description": "Expand your repertoire by tackling something new each week.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 1,
                        "duration": 60,
                        "tags": "learning, songs, repertoire",
                    },
                    {
                        "title": "Study music theory",
                        "description": "Understand chord progressions, scales, and composition techniques.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 2,
                        "duration": 30,
                        "tags": "theory, learning, musicianship",
                    },
                    {
                        "title": "Record and review your playing",
                        "description": "Record yourself to identify areas for improvement objectively.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 2,
                        "duration": 30,
                        "tags": "recording, review, improvement",
                    },
                    {
                        "title": "Jam with other musicians",
                        "description": "Play with others to improve timing, listening, and collaborative skills.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 1,
                        "duration": 90,
                        "tags": "jamming, collaboration, social",
                    },
                    {
                        "title": "Write an original song or composition",
                        "description": "Express yourself by creating your own music.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 1,
                        "duration": 60,
                        "tags": "songwriting, composition, creativity",
                    },
                    {
                        "title": "Perform at open mic or local venue",
                        "description": "Get stage experience and overcome performance anxiety.",
                        "priority": "urgent",
                        "period": "monthly",
                        "target": 2,
                        "duration": 120,
                        "tags": "performance, stage, experience",
                    },
                    {
                        "title": "Prepare for audition or competition",
                        "description": "Polish your best pieces for a high-stakes performance opportunity.",
                        "priority": "urgent",
                        "period": "weekly",
                        "target": 5,
                        "duration": 90,
                        "tags": "audition, competition, ambitious",
                    },
                ],
            },
            # User 9: Social & Relationships
            {
                "user": {
                    "username": "robert_anderson",
                    "email": "robert@example.com",
                    "first_name": "Robert",
                    "last_name": "Anderson",
                },
                "tasks": [
                    {
                        "title": "Send a thoughtful message to a friend",
                        "description": "Reach out to someone you haven't talked to in a while.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 5,
                        "tags": "friendship, communication, connection",
                    },
                    {
                        "title": "Practice active listening",
                        "description": "In conversations, focus fully on the other person without planning your response.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 15,
                        "tags": "listening, communication, presence",
                    },
                    {
                        "title": "Have a phone call with family",
                        "description": "Stay connected with parents, siblings, or relatives through regular calls.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 2,
                        "duration": 30,
                        "tags": "family, connection, relationships",
                    },
                    {
                        "title": "Plan a social activity",
                        "description": "Organize dinner, game night, or outing with friends.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 1,
                        "duration": 30,
                        "tags": "social, planning, friends",
                    },
                    {
                        "title": "Meet someone new",
                        "description": "Attend a meetup, class, or event to expand your social circle.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 1,
                        "duration": 90,
                        "tags": "networking, meetup, new-people",
                    },
                    {
                        "title": "Practice a random act of kindness",
                        "description": "Do something nice for a stranger or acquaintance without expecting anything back.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 2,
                        "duration": 15,
                        "tags": "kindness, generosity, community",
                    },
                    {
                        "title": "Have a deep conversation",
                        "description": "Go beyond small talk - discuss dreams, fears, and meaningful topics.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 1,
                        "duration": 60,
                        "tags": "conversation, depth, connection",
                    },
                    {
                        "title": "Resolve a conflict or apologize",
                        "description": "Address any tension in relationships with honesty and empathy.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 1,
                        "duration": 30,
                        "tags": "conflict, resolution, growth",
                    },
                    {
                        "title": "Volunteer for a cause",
                        "description": "Give your time to help others through a charity or community organization.",
                        "priority": "urgent",
                        "period": "weekly",
                        "target": 1,
                        "duration": 180,
                        "tags": "volunteering, community, giving",
                    },
                    {
                        "title": "Host a gathering or party",
                        "description": "Bring people together by organizing a memorable event at your home.",
                        "priority": "urgent",
                        "period": "monthly",
                        "target": 1,
                        "duration": 240,
                        "tags": "hosting, party, social",
                    },
                ],
            },
            # User 10: Entrepreneur & Business
            {
                "user": {
                    "username": "lisa_thomas",
                    "email": "lisa@example.com",
                    "first_name": "Lisa",
                    "last_name": "Thomas",
                },
                "tasks": [
                    {
                        "title": "Review key business metrics",
                        "description": "Check dashboard for revenue, users, or other KPIs daily.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 10,
                        "tags": "metrics, analytics, business",
                    },
                    {
                        "title": "Respond to customer inquiries",
                        "description": "Provide excellent support by addressing customer questions promptly.",
                        "priority": "low",
                        "period": "daily",
                        "target": 1,
                        "duration": 30,
                        "tags": "customer, support, service",
                    },
                    {
                        "title": "Create content for social media",
                        "description": "Build brand presence with valuable posts on LinkedIn, Twitter, or Instagram.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 3,
                        "duration": 30,
                        "tags": "content, social-media, marketing",
                    },
                    {
                        "title": "Network with other entrepreneurs",
                        "description": "Attend startup events or schedule calls with fellow founders.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 2,
                        "duration": 60,
                        "tags": "networking, founders, community",
                    },
                    {
                        "title": "Work on product improvements",
                        "description": "Based on user feedback, enhance your product or service.",
                        "priority": "medium",
                        "period": "weekly",
                        "target": 3,
                        "duration": 120,
                        "tags": "product, improvement, development",
                    },
                    {
                        "title": "Study competitors and market",
                        "description": "Analyze what competitors are doing and identify market opportunities.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 1,
                        "duration": 60,
                        "tags": "research, competitors, market",
                    },
                    {
                        "title": "Reach out to potential customers",
                        "description": "Cold outreach to leads through email, LinkedIn, or calls.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 5,
                        "duration": 60,
                        "tags": "sales, outreach, growth",
                    },
                    {
                        "title": "Write and send newsletter",
                        "description": "Keep your audience engaged with valuable email content.",
                        "priority": "high",
                        "period": "weekly",
                        "target": 1,
                        "duration": 60,
                        "tags": "newsletter, email, marketing",
                    },
                    {
                        "title": "Pitch to investors or partners",
                        "description": "Present your business to potential investors or strategic partners.",
                        "priority": "urgent",
                        "period": "weekly",
                        "target": 1,
                        "duration": 90,
                        "tags": "pitch, investors, fundraising",
                    },
                    {
                        "title": "Achieve monthly revenue target",
                        "description": "Focus on sales and retention to hit your MRR or revenue goals.",
                        "priority": "urgent",
                        "period": "weekly",
                        "target": 5,
                        "duration": 120,
                        "tags": "revenue, goals, ambitious",
                    },
                ],
            },
        ]

        priority_map = {
            "low": Task.Priority.LOW,
            "medium": Task.Priority.MEDIUM,
            "high": Task.Priority.HIGH,
            "urgent": Task.Priority.URGENT,
        }

        period_map = {
            "daily": Task.RecurrencePeriod.DAILY,
            "weekly": Task.RecurrencePeriod.WEEKLY,
            "monthly": Task.RecurrencePeriod.MONTHLY,
        }

        created_users = 0
        created_tasks = 0

        for user_data in users_with_tasks:
            # Create user
            user_info = user_data["user"]
            user, created = User.objects.get_or_create(
                username=user_info["username"],
                defaults={
                    "email": user_info["email"],
                    "first_name": user_info["first_name"],
                    "last_name": user_info["last_name"],
                },
            )
            if created:
                user.set_password("password123")
                user.save()
                created_users += 1
                self.stdout.write(f"  Created user: {user.username}")
            else:
                self.stdout.write(f"  User already exists: {user.username}")

            # Create tasks for this user
            for i, task_info in enumerate(user_data["tasks"]):
                existing = Task.objects.filter(user=user, title=task_info["title"]).exists()
                if existing:
                    continue

                days_offset = (i + 1) * 7

                task = Task.objects.create(
                    user=user,
                    title=task_info["title"],
                    description=task_info["description"],
                    priority=priority_map[task_info["priority"]],
                    status=Task.Status.TODO if i < 5 else Task.Status.IN_PROGRESS,
                    is_recurring=True,
                    recurrence_period=period_map[task_info["period"]],
                    recurrence_target_count=task_info["target"],
                    estimated_duration=task_info["duration"],
                    tags=task_info["tags"],
                    due_date=timezone.now() + timedelta(days=days_offset),
                )
                created_tasks += 1

                # Add completions for easier tasks
                if i < 4:
                    for j in range(min(i + 1, 3)):
                        TaskCompletion.objects.create(
                            task=task,
                            notes=f"Completed session {j + 1}",
                            duration_minutes=task_info["duration"],
                        )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Successfully created {created_users} users"))
        self.stdout.write(self.style.SUCCESS(f"Successfully created {created_tasks} tasks"))
        self.stdout.write("")
        self.stdout.write("Sample login credentials:")
        self.stdout.write("  Username: john_doe (or any other)")
        self.stdout.write("  Password: password123")
        self.stdout.write("")
        self.stdout.write("User focus areas:")
        self.stdout.write("  john_doe      - Fitness Enthusiast")
        self.stdout.write("  jane_smith    - Tech Professional")
        self.stdout.write("  mike_wilson   - Language Learner")
        self.stdout.write("  sarah_jones   - Mindfulness & Mental Health")
        self.stdout.write("  david_brown   - Creative Artist")
        self.stdout.write("  emily_davis   - Financial Growth")
        self.stdout.write("  chris_miller  - Career Professional")
        self.stdout.write("  amanda_taylor - Music & Performing Arts")
        self.stdout.write("  robert_anderson - Social & Relationships")
        self.stdout.write("  lisa_thomas   - Entrepreneur & Business")
