-- =============================================================================
-- Seed Data for Self Development App
-- Creates 10 users with unique tasks for each
-- Password for all users: password123
-- =============================================================================

-- Password hash for 'password123' (pbkdf2_sha256)
-- Generated using Django's make_password('password123')
\set password_hash 'pbkdf2_sha256$720000$3ami6B5cYWTxX8aT$yAwUnTBG7C+X5OG0OZS2aM51EsuGrdE32KK6Xe07Ark='

-- =============================================================================
-- USERS
-- =============================================================================

INSERT INTO auth_user (username, email, first_name, last_name, password, is_active, date_joined) VALUES
    ('john_doe', 'john@example.com', 'John', 'Doe', :'password_hash', TRUE, NOW()),
    ('jane_smith', 'jane@example.com', 'Jane', 'Smith', :'password_hash', TRUE, NOW()),
    ('mike_wilson', 'mike@example.com', 'Mike', 'Wilson', :'password_hash', TRUE, NOW()),
    ('sarah_jones', 'sarah@example.com', 'Sarah', 'Jones', :'password_hash', TRUE, NOW()),
    ('david_brown', 'david@example.com', 'David', 'Brown', :'password_hash', TRUE, NOW()),
    ('emily_davis', 'emily@example.com', 'Emily', 'Davis', :'password_hash', TRUE, NOW()),
    ('chris_miller', 'chris@example.com', 'Chris', 'Miller', :'password_hash', TRUE, NOW()),
    ('amanda_taylor', 'amanda@example.com', 'Amanda', 'Taylor', :'password_hash', TRUE, NOW()),
    ('robert_anderson', 'robert@example.com', 'Robert', 'Anderson', :'password_hash', TRUE, NOW()),
    ('lisa_thomas', 'lisa@example.com', 'Lisa', 'Thomas', :'password_hash', TRUE, NOW())
ON CONFLICT (username) DO NOTHING;

-- =============================================================================
-- TASKS - User 1: John Doe (Fitness Enthusiast)
-- =============================================================================

INSERT INTO tasks_task (user_id, title, description, priority, status, is_recurring, recurrence_period, recurrence_target_count, estimated_duration, tags, due_date) VALUES
    ((SELECT id FROM auth_user WHERE username = 'john_doe'), 'Morning stretching routine', 'Start each day with 10 minutes of stretching to improve flexibility.', 'low', 'todo', TRUE, 'daily', 1, 10, 'fitness, morning, flexibility', NOW() + INTERVAL '7 days'),
    ((SELECT id FROM auth_user WHERE username = 'john_doe'), 'Track daily calories intake', 'Log all meals in MyFitnessPal to maintain awareness of nutrition.', 'low', 'todo', TRUE, 'daily', 1, 5, 'nutrition, tracking, health', NOW() + INTERVAL '14 days'),
    ((SELECT id FROM auth_user WHERE username = 'john_doe'), 'Drink protein shake after workout', 'Consume 30g protein within 30 minutes post-exercise for muscle recovery.', 'medium', 'todo', TRUE, 'weekly', 4, 5, 'nutrition, protein, recovery', NOW() + INTERVAL '21 days'),
    ((SELECT id FROM auth_user WHERE username = 'john_doe'), 'Complete strength training session', 'Full body workout focusing on compound movements: squats, deadlifts, bench press.', 'medium', 'todo', TRUE, 'weekly', 3, 60, 'strength, gym, workout', NOW() + INTERVAL '28 days'),
    ((SELECT id FROM auth_user WHERE username = 'john_doe'), 'Run 5K without stopping', 'Build cardiovascular endurance by running 5 kilometers continuously.', 'medium', 'todo', TRUE, 'weekly', 2, 30, 'running, cardio, endurance', NOW() + INTERVAL '35 days'),
    ((SELECT id FROM auth_user WHERE username = 'john_doe'), 'Try a new healthy recipe', 'Experiment with nutritious cooking - focus on high protein, low processed foods.', 'medium', 'in_progress', TRUE, 'weekly', 1, 45, 'cooking, nutrition, health', NOW() + INTERVAL '42 days'),
    ((SELECT id FROM auth_user WHERE username = 'john_doe'), 'Achieve 10,000 steps daily', 'Stay active throughout the day by walking more and taking stairs.', 'high', 'in_progress', TRUE, 'daily', 1, 60, 'walking, activity, health', NOW() + INTERVAL '49 days'),
    ((SELECT id FROM auth_user WHERE username = 'john_doe'), 'Master a new exercise form', 'Learn proper technique for Olympic lifts or advanced calisthenics moves.', 'high', 'in_progress', TRUE, 'weekly', 2, 30, 'technique, learning, fitness', NOW() + INTERVAL '56 days'),
    ((SELECT id FROM auth_user WHERE username = 'john_doe'), 'Complete a fitness challenge', '30-day challenge: 100 pushups, 100 squats, 100 situps daily.', 'urgent', 'in_progress', TRUE, 'daily', 1, 45, 'challenge, discipline, strength', NOW() + INTERVAL '63 days'),
    ((SELECT id FROM auth_user WHERE username = 'john_doe'), 'Train for half-marathon', 'Follow a structured 12-week training plan to run 21.1km.', 'urgent', 'in_progress', TRUE, 'weekly', 4, 90, 'marathon, running, ambitious', NOW() + INTERVAL '70 days');

-- =============================================================================
-- TASKS - User 2: Jane Smith (Tech Professional)
-- =============================================================================

INSERT INTO tasks_task (user_id, title, description, priority, status, is_recurring, recurrence_period, recurrence_target_count, estimated_duration, tags, due_date) VALUES
    ((SELECT id FROM auth_user WHERE username = 'jane_smith'), 'Review tech news and updates', 'Spend 10 minutes reading Hacker News or TechCrunch to stay informed.', 'low', 'todo', TRUE, 'daily', 1, 10, 'tech, news, learning', NOW() + INTERVAL '7 days'),
    ((SELECT id FROM auth_user WHERE username = 'jane_smith'), 'Practice typing speed', 'Use keybr.com or typing.com to improve typing to 80+ WPM.', 'low', 'todo', TRUE, 'daily', 1, 10, 'typing, productivity, skill', NOW() + INTERVAL '14 days'),
    ((SELECT id FROM auth_user WHERE username = 'jane_smith'), 'Solve one coding challenge', 'Complete a LeetCode or HackerRank problem to sharpen algorithms.', 'medium', 'todo', TRUE, 'daily', 1, 30, 'coding, algorithms, practice', NOW() + INTERVAL '21 days'),
    ((SELECT id FROM auth_user WHERE username = 'jane_smith'), 'Contribute to open source', 'Submit a PR or fix a bug in an open source project on GitHub.', 'medium', 'todo', TRUE, 'weekly', 1, 60, 'opensource, github, community', NOW() + INTERVAL '28 days'),
    ((SELECT id FROM auth_user WHERE username = 'jane_smith'), 'Learn a new programming concept', 'Study design patterns, system design, or new language features.', 'medium', 'todo', TRUE, 'weekly', 2, 45, 'learning, programming, concepts', NOW() + INTERVAL '35 days'),
    ((SELECT id FROM auth_user WHERE username = 'jane_smith'), 'Build a personal project feature', 'Add functionality to your portfolio project or side hustle app.', 'high', 'in_progress', TRUE, 'weekly', 3, 90, 'project, coding, portfolio', NOW() + INTERVAL '42 days'),
    ((SELECT id FROM auth_user WHERE username = 'jane_smith'), 'Write a technical blog post', 'Share knowledge by writing about a problem you solved or technology you learned.', 'high', 'in_progress', TRUE, 'monthly', 2, 120, 'writing, blog, teaching', NOW() + INTERVAL '49 days'),
    ((SELECT id FROM auth_user WHERE username = 'jane_smith'), 'Complete AWS certification module', 'Study for AWS Solutions Architect or similar cloud certification.', 'high', 'in_progress', TRUE, 'weekly', 3, 60, 'aws, certification, cloud', NOW() + INTERVAL '56 days'),
    ((SELECT id FROM auth_user WHERE username = 'jane_smith'), 'Mentor a junior developer', 'Schedule pair programming or code review sessions with less experienced colleagues.', 'urgent', 'in_progress', TRUE, 'weekly', 1, 60, 'mentoring, leadership, teaching', NOW() + INTERVAL '63 days'),
    ((SELECT id FROM auth_user WHERE username = 'jane_smith'), 'Build and deploy a SaaS product', 'Create a complete product from idea to production with paying customers.', 'urgent', 'in_progress', TRUE, 'weekly', 5, 120, 'saas, entrepreneurship, ambitious', NOW() + INTERVAL '70 days');

-- =============================================================================
-- TASKS - User 3: Mike Wilson (Language Learner)
-- =============================================================================

INSERT INTO tasks_task (user_id, title, description, priority, status, is_recurring, recurrence_period, recurrence_target_count, estimated_duration, tags, due_date) VALUES
    ((SELECT id FROM auth_user WHERE username = 'mike_wilson'), 'Review flashcards on Anki', 'Spend 10 minutes reviewing vocabulary flashcards using spaced repetition.', 'low', 'todo', TRUE, 'daily', 1, 10, 'vocabulary, anki, memory', NOW() + INTERVAL '7 days'),
    ((SELECT id FROM auth_user WHERE username = 'mike_wilson'), 'Listen to a podcast in target language', 'Immerse yourself by listening to native content during commute or exercise.', 'low', 'todo', TRUE, 'daily', 1, 20, 'listening, podcast, immersion', NOW() + INTERVAL '14 days'),
    ((SELECT id FROM auth_user WHERE username = 'mike_wilson'), 'Complete Duolingo daily goal', 'Maintain your streak by completing at least one lesson.', 'medium', 'todo', TRUE, 'daily', 1, 15, 'duolingo, practice, streak', NOW() + INTERVAL '21 days'),
    ((SELECT id FROM auth_user WHERE username = 'mike_wilson'), 'Watch a movie without subtitles', 'Challenge your comprehension by watching foreign films without English subtitles.', 'medium', 'todo', TRUE, 'weekly', 1, 120, 'movies, listening, comprehension', NOW() + INTERVAL '28 days'),
    ((SELECT id FROM auth_user WHERE username = 'mike_wilson'), 'Practice speaking with language partner', 'Use iTalki or Tandem to have a 30-minute conversation with a native speaker.', 'medium', 'todo', TRUE, 'weekly', 2, 30, 'speaking, conversation, practice', NOW() + INTERVAL '35 days'),
    ((SELECT id FROM auth_user WHERE username = 'mike_wilson'), 'Read a book chapter in target language', 'Improve reading comprehension by tackling native literature.', 'high', 'in_progress', TRUE, 'weekly', 3, 45, 'reading, books, comprehension', NOW() + INTERVAL '42 days'),
    ((SELECT id FROM auth_user WHERE username = 'mike_wilson'), 'Write a journal entry in target language', 'Practice writing by describing your day or thoughts in the language you are learning.', 'high', 'in_progress', TRUE, 'daily', 1, 15, 'writing, journal, practice', NOW() + INTERVAL '49 days'),
    ((SELECT id FROM auth_user WHERE username = 'mike_wilson'), 'Learn 20 new vocabulary words', 'Expand your vocabulary systematically with context and example sentences.', 'high', 'in_progress', TRUE, 'weekly', 1, 30, 'vocabulary, learning, words', NOW() + INTERVAL '56 days'),
    ((SELECT id FROM auth_user WHERE username = 'mike_wilson'), 'Take an online language class', 'Enroll in structured lessons with a professional teacher for grammar and conversation.', 'urgent', 'in_progress', TRUE, 'weekly', 2, 60, 'class, teacher, structured', NOW() + INTERVAL '63 days'),
    ((SELECT id FROM auth_user WHERE username = 'mike_wilson'), 'Achieve B2 certification level', 'Prepare for and pass an official language proficiency exam (DELF, JLPT, HSK, etc.).', 'urgent', 'in_progress', TRUE, 'weekly', 5, 90, 'certification, exam, fluency', NOW() + INTERVAL '70 days');

-- =============================================================================
-- TASKS - User 4: Sarah Jones (Mindfulness & Mental Health)
-- =============================================================================

INSERT INTO tasks_task (user_id, title, description, priority, status, is_recurring, recurrence_period, recurrence_target_count, estimated_duration, tags, due_date) VALUES
    ((SELECT id FROM auth_user WHERE username = 'sarah_jones'), 'Practice deep breathing exercises', 'Take 5 minutes for box breathing or 4-7-8 technique to reduce stress.', 'low', 'todo', TRUE, 'daily', 2, 5, 'breathing, relaxation, stress', NOW() + INTERVAL '7 days'),
    ((SELECT id FROM auth_user WHERE username = 'sarah_jones'), 'Write three gratitude items', 'Before bed, write down three things you are grateful for today.', 'low', 'todo', TRUE, 'daily', 1, 5, 'gratitude, journaling, positivity', NOW() + INTERVAL '14 days'),
    ((SELECT id FROM auth_user WHERE username = 'sarah_jones'), 'Morning meditation session', 'Start the day with guided meditation using Headspace or Calm app.', 'medium', 'todo', TRUE, 'daily', 1, 15, 'meditation, morning, mindfulness', NOW() + INTERVAL '21 days'),
    ((SELECT id FROM auth_user WHERE username = 'sarah_jones'), 'Digital detox hour', 'Spend one hour without any screens - read, walk, or simply be present.', 'medium', 'todo', TRUE, 'daily', 1, 60, 'detox, screens, presence', NOW() + INTERVAL '28 days'),
    ((SELECT id FROM auth_user WHERE username = 'sarah_jones'), 'Practice yoga or tai chi', 'Combine physical movement with mindfulness through gentle exercise.', 'medium', 'todo', TRUE, 'weekly', 3, 45, 'yoga, movement, mindfulness', NOW() + INTERVAL '35 days'),
    ((SELECT id FROM auth_user WHERE username = 'sarah_jones'), 'Journal about emotions and thoughts', 'Free-write about your feelings to process and understand them better.', 'high', 'in_progress', TRUE, 'daily', 1, 20, 'journaling, emotions, reflection', NOW() + INTERVAL '42 days'),
    ((SELECT id FROM auth_user WHERE username = 'sarah_jones'), 'Spend quality time in nature', 'Go for a mindful walk in a park, forest, or near water.', 'high', 'in_progress', TRUE, 'weekly', 2, 60, 'nature, walking, peace', NOW() + INTERVAL '49 days'),
    ((SELECT id FROM auth_user WHERE username = 'sarah_jones'), 'Read a self-help or psychology book', 'Learn about mental health, habits, or personal growth from experts.', 'high', 'in_progress', TRUE, 'weekly', 1, 30, 'reading, psychology, growth', NOW() + INTERVAL '56 days'),
    ((SELECT id FROM auth_user WHERE username = 'sarah_jones'), 'Attend a therapy or coaching session', 'Work with a professional to address challenges and set goals.', 'urgent', 'in_progress', TRUE, 'weekly', 1, 60, 'therapy, coaching, professional', NOW() + INTERVAL '63 days'),
    ((SELECT id FROM auth_user WHERE username = 'sarah_jones'), 'Complete a 30-day meditation challenge', 'Build a solid meditation practice by committing to 30 consecutive days.', 'urgent', 'in_progress', TRUE, 'daily', 1, 20, 'challenge, meditation, habit', NOW() + INTERVAL '70 days');

-- =============================================================================
-- TASKS - User 5: David Brown (Creative Artist)
-- =============================================================================

INSERT INTO tasks_task (user_id, title, description, priority, status, is_recurring, recurrence_period, recurrence_target_count, estimated_duration, tags, due_date) VALUES
    ((SELECT id FROM auth_user WHERE username = 'david_brown'), 'Daily sketch practice', 'Draw anything for 15 minutes - people, objects, or abstract shapes.', 'low', 'todo', TRUE, 'daily', 1, 15, 'drawing, sketch, practice', NOW() + INTERVAL '7 days'),
    ((SELECT id FROM auth_user WHERE username = 'david_brown'), 'Explore a new art technique', 'Watch a tutorial and try watercolors, charcoal, or digital art.', 'low', 'todo', TRUE, 'weekly', 1, 30, 'technique, learning, experimentation', NOW() + INTERVAL '14 days'),
    ((SELECT id FROM auth_user WHERE username = 'david_brown'), 'Take reference photos', 'Photograph interesting subjects, textures, and compositions for future artwork.', 'medium', 'todo', TRUE, 'weekly', 2, 30, 'photography, reference, inspiration', NOW() + INTERVAL '21 days'),
    ((SELECT id FROM auth_user WHERE username = 'david_brown'), 'Study art from masters', 'Analyze works by famous artists - understand composition, color, and technique.', 'medium', 'todo', TRUE, 'weekly', 1, 45, 'study, masters, analysis', NOW() + INTERVAL '28 days'),
    ((SELECT id FROM auth_user WHERE username = 'david_brown'), 'Work on a larger art piece', 'Dedicate focused time to a more ambitious artwork that takes multiple sessions.', 'medium', 'todo', TRUE, 'weekly', 3, 90, 'artwork, project, creation', NOW() + INTERVAL '35 days'),
    ((SELECT id FROM auth_user WHERE username = 'david_brown'), 'Share art on social media', 'Post your work on Instagram or ArtStation to build an audience and get feedback.', 'high', 'in_progress', TRUE, 'weekly', 2, 15, 'social, sharing, community', NOW() + INTERVAL '42 days'),
    ((SELECT id FROM auth_user WHERE username = 'david_brown'), 'Participate in an art challenge', 'Join Inktober, Draw This In Your Style, or similar community challenges.', 'high', 'in_progress', TRUE, 'weekly', 3, 60, 'challenge, community, practice', NOW() + INTERVAL '49 days'),
    ((SELECT id FROM auth_user WHERE username = 'david_brown'), 'Create art for a client or commission', 'Take on paid work to build portfolio and earn from your skills.', 'high', 'in_progress', TRUE, 'monthly', 1, 180, 'commission, client, professional', NOW() + INTERVAL '56 days'),
    ((SELECT id FROM auth_user WHERE username = 'david_brown'), 'Attend a life drawing session', 'Practice figure drawing with live models to improve human anatomy skills.', 'urgent', 'in_progress', TRUE, 'weekly', 1, 120, 'figure, anatomy, live', NOW() + INTERVAL '63 days'),
    ((SELECT id FROM auth_user WHERE username = 'david_brown'), 'Prepare portfolio for gallery submission', 'Curate your best work for exhibition opportunities or art school applications.', 'urgent', 'in_progress', TRUE, 'weekly', 2, 60, 'portfolio, gallery, ambitious', NOW() + INTERVAL '70 days');

-- =============================================================================
-- TASKS - User 6: Emily Davis (Financial Growth)
-- =============================================================================

INSERT INTO tasks_task (user_id, title, description, priority, status, is_recurring, recurrence_period, recurrence_target_count, estimated_duration, tags, due_date) VALUES
    ((SELECT id FROM auth_user WHERE username = 'emily_davis'), 'Track daily expenses', 'Log every purchase in a budgeting app like YNAB or Mint.', 'low', 'todo', TRUE, 'daily', 1, 5, 'budget, tracking, expenses', NOW() + INTERVAL '7 days'),
    ((SELECT id FROM auth_user WHERE username = 'emily_davis'), 'Review financial news', 'Stay informed about markets and economy with Bloomberg or WSJ.', 'low', 'todo', TRUE, 'daily', 1, 10, 'news, markets, finance', NOW() + INTERVAL '14 days'),
    ((SELECT id FROM auth_user WHERE username = 'emily_davis'), 'Transfer to savings account', 'Automate weekly savings by moving money to a high-yield savings account.', 'medium', 'todo', TRUE, 'weekly', 1, 5, 'savings, automation, wealth', NOW() + INTERVAL '21 days'),
    ((SELECT id FROM auth_user WHERE username = 'emily_davis'), 'Review and categorize spending', 'Analyze where your money goes and identify areas to cut back.', 'medium', 'todo', TRUE, 'weekly', 1, 30, 'budget, analysis, spending', NOW() + INTERVAL '28 days'),
    ((SELECT id FROM auth_user WHERE username = 'emily_davis'), 'Research investment opportunities', 'Study stocks, ETFs, or real estate options for growing wealth.', 'medium', 'todo', TRUE, 'weekly', 2, 45, 'investing, research, stocks', NOW() + INTERVAL '35 days'),
    ((SELECT id FROM auth_user WHERE username = 'emily_davis'), 'Read a personal finance book', 'Learn from experts like Ramit Sethi, Dave Ramsey, or Morgan Housel.', 'high', 'in_progress', TRUE, 'weekly', 1, 30, 'reading, finance, education', NOW() + INTERVAL '42 days'),
    ((SELECT id FROM auth_user WHERE username = 'emily_davis'), 'Rebalance investment portfolio', 'Review asset allocation and adjust to maintain your target risk level.', 'high', 'in_progress', TRUE, 'monthly', 1, 60, 'portfolio, investing, rebalance', NOW() + INTERVAL '49 days'),
    ((SELECT id FROM auth_user WHERE username = 'emily_davis'), 'Negotiate a bill or subscription', 'Call service providers to reduce rates or cancel unused subscriptions.', 'high', 'in_progress', TRUE, 'monthly', 2, 30, 'negotiation, savings, bills', NOW() + INTERVAL '56 days'),
    ((SELECT id FROM auth_user WHERE username = 'emily_davis'), 'Create additional income stream', 'Start a side hustle, freelancing, or passive income project.', 'urgent', 'in_progress', TRUE, 'weekly', 3, 120, 'income, side-hustle, entrepreneurship', NOW() + INTERVAL '63 days'),
    ((SELECT id FROM auth_user WHERE username = 'emily_davis'), 'Plan for financial independence', 'Calculate FIRE number and create a long-term wealth building strategy.', 'urgent', 'in_progress', TRUE, 'weekly', 2, 60, 'fire, independence, planning', NOW() + INTERVAL '70 days');

-- =============================================================================
-- TASKS - User 7: Chris Miller (Career Professional)
-- =============================================================================

INSERT INTO tasks_task (user_id, title, description, priority, status, is_recurring, recurrence_period, recurrence_target_count, estimated_duration, tags, due_date) VALUES
    ((SELECT id FROM auth_user WHERE username = 'chris_miller'), 'Organize inbox and respond to emails', 'Achieve inbox zero by processing and responding to all important emails.', 'low', 'todo', TRUE, 'daily', 1, 20, 'email, organization, productivity', NOW() + INTERVAL '7 days'),
    ((SELECT id FROM auth_user WHERE username = 'chris_miller'), 'Plan tomorrow priorities', 'End each workday by listing top 3 tasks for the next day.', 'low', 'todo', TRUE, 'daily', 1, 10, 'planning, priorities, productivity', NOW() + INTERVAL '14 days'),
    ((SELECT id FROM auth_user WHERE username = 'chris_miller'), 'Update LinkedIn profile', 'Keep your professional profile current with recent achievements and skills.', 'medium', 'todo', TRUE, 'monthly', 1, 30, 'linkedin, profile, networking', NOW() + INTERVAL '21 days'),
    ((SELECT id FROM auth_user WHERE username = 'chris_miller'), 'Connect with a colleague', 'Build relationships by having coffee or a virtual chat with coworkers.', 'medium', 'todo', TRUE, 'weekly', 2, 30, 'networking, relationships, colleagues', NOW() + INTERVAL '28 days'),
    ((SELECT id FROM auth_user WHERE username = 'chris_miller'), 'Attend industry webinar or event', 'Stay current by participating in professional development events.', 'medium', 'todo', TRUE, 'weekly', 1, 60, 'webinar, industry, learning', NOW() + INTERVAL '35 days'),
    ((SELECT id FROM auth_user WHERE username = 'chris_miller'), 'Document accomplishments for review', 'Keep a brag document of your wins and contributions.', 'high', 'in_progress', TRUE, 'weekly', 1, 15, 'accomplishments, review, career', NOW() + INTERVAL '42 days'),
    ((SELECT id FROM auth_user WHERE username = 'chris_miller'), 'Practice public speaking', 'Join Toastmasters or practice presentations to improve communication.', 'high', 'in_progress', TRUE, 'weekly', 1, 60, 'speaking, presentation, communication', NOW() + INTERVAL '49 days'),
    ((SELECT id FROM auth_user WHERE username = 'chris_miller'), 'Seek feedback from manager', 'Schedule regular 1:1s to discuss performance and growth areas.', 'high', 'in_progress', TRUE, 'weekly', 1, 30, 'feedback, manager, growth', NOW() + INTERVAL '56 days'),
    ((SELECT id FROM auth_user WHERE username = 'chris_miller'), 'Apply for stretch assignments', 'Volunteer for challenging projects that expand your skills and visibility.', 'urgent', 'in_progress', TRUE, 'monthly', 1, 60, 'growth, projects, visibility', NOW() + INTERVAL '63 days'),
    ((SELECT id FROM auth_user WHERE username = 'chris_miller'), 'Prepare for promotion conversation', 'Build your case with evidence and schedule a career discussion with leadership.', 'urgent', 'in_progress', TRUE, 'weekly', 2, 60, 'promotion, career, ambitious', NOW() + INTERVAL '70 days');

-- =============================================================================
-- TASKS - User 8: Amanda Taylor (Music & Performing Arts)
-- =============================================================================

INSERT INTO tasks_task (user_id, title, description, priority, status, is_recurring, recurrence_period, recurrence_target_count, estimated_duration, tags, due_date) VALUES
    ((SELECT id FROM auth_user WHERE username = 'amanda_taylor'), 'Warm up voice or instrument', 'Start practice with scales, arpeggios, or vocal exercises.', 'low', 'todo', TRUE, 'daily', 1, 15, 'warmup, practice, technique', NOW() + INTERVAL '7 days'),
    ((SELECT id FROM auth_user WHERE username = 'amanda_taylor'), 'Listen to new music for inspiration', 'Discover new artists and genres to expand your musical horizons.', 'low', 'todo', TRUE, 'daily', 1, 20, 'listening, inspiration, discovery', NOW() + INTERVAL '14 days'),
    ((SELECT id FROM auth_user WHERE username = 'amanda_taylor'), 'Practice current repertoire', 'Work on pieces you are learning with focus on difficult passages.', 'medium', 'todo', TRUE, 'daily', 1, 45, 'practice, repertoire, improvement', NOW() + INTERVAL '21 days'),
    ((SELECT id FROM auth_user WHERE username = 'amanda_taylor'), 'Learn a new song or piece', 'Expand your repertoire by tackling something new each week.', 'medium', 'todo', TRUE, 'weekly', 1, 60, 'learning, songs, repertoire', NOW() + INTERVAL '28 days'),
    ((SELECT id FROM auth_user WHERE username = 'amanda_taylor'), 'Study music theory', 'Understand chord progressions, scales, and composition techniques.', 'medium', 'todo', TRUE, 'weekly', 2, 30, 'theory, learning, musicianship', NOW() + INTERVAL '35 days'),
    ((SELECT id FROM auth_user WHERE username = 'amanda_taylor'), 'Record and review your playing', 'Record yourself to identify areas for improvement objectively.', 'high', 'in_progress', TRUE, 'weekly', 2, 30, 'recording, review, improvement', NOW() + INTERVAL '42 days'),
    ((SELECT id FROM auth_user WHERE username = 'amanda_taylor'), 'Jam with other musicians', 'Play with others to improve timing, listening, and collaborative skills.', 'high', 'in_progress', TRUE, 'weekly', 1, 90, 'jamming, collaboration, social', NOW() + INTERVAL '49 days'),
    ((SELECT id FROM auth_user WHERE username = 'amanda_taylor'), 'Write an original song or composition', 'Express yourself by creating your own music.', 'high', 'in_progress', TRUE, 'weekly', 1, 60, 'songwriting, composition, creativity', NOW() + INTERVAL '56 days'),
    ((SELECT id FROM auth_user WHERE username = 'amanda_taylor'), 'Perform at open mic or local venue', 'Get stage experience and overcome performance anxiety.', 'urgent', 'in_progress', TRUE, 'monthly', 2, 120, 'performance, stage, experience', NOW() + INTERVAL '63 days'),
    ((SELECT id FROM auth_user WHERE username = 'amanda_taylor'), 'Prepare for audition or competition', 'Polish your best pieces for a high-stakes performance opportunity.', 'urgent', 'in_progress', TRUE, 'weekly', 5, 90, 'audition, competition, ambitious', NOW() + INTERVAL '70 days');

-- =============================================================================
-- TASKS - User 9: Robert Anderson (Social & Relationships)
-- =============================================================================

INSERT INTO tasks_task (user_id, title, description, priority, status, is_recurring, recurrence_period, recurrence_target_count, estimated_duration, tags, due_date) VALUES
    ((SELECT id FROM auth_user WHERE username = 'robert_anderson'), 'Send a thoughtful message to a friend', 'Reach out to someone you have not talked to in a while.', 'low', 'todo', TRUE, 'daily', 1, 5, 'friendship, communication, connection', NOW() + INTERVAL '7 days'),
    ((SELECT id FROM auth_user WHERE username = 'robert_anderson'), 'Practice active listening', 'In conversations, focus fully on the other person without planning your response.', 'low', 'todo', TRUE, 'daily', 1, 15, 'listening, communication, presence', NOW() + INTERVAL '14 days'),
    ((SELECT id FROM auth_user WHERE username = 'robert_anderson'), 'Have a phone call with family', 'Stay connected with parents, siblings, or relatives through regular calls.', 'medium', 'todo', TRUE, 'weekly', 2, 30, 'family, connection, relationships', NOW() + INTERVAL '21 days'),
    ((SELECT id FROM auth_user WHERE username = 'robert_anderson'), 'Plan a social activity', 'Organize dinner, game night, or outing with friends.', 'medium', 'todo', TRUE, 'weekly', 1, 30, 'social, planning, friends', NOW() + INTERVAL '28 days'),
    ((SELECT id FROM auth_user WHERE username = 'robert_anderson'), 'Meet someone new', 'Attend a meetup, class, or event to expand your social circle.', 'medium', 'todo', TRUE, 'weekly', 1, 90, 'networking, meetup, new-people', NOW() + INTERVAL '35 days'),
    ((SELECT id FROM auth_user WHERE username = 'robert_anderson'), 'Practice a random act of kindness', 'Do something nice for a stranger or acquaintance without expecting anything back.', 'high', 'in_progress', TRUE, 'weekly', 2, 15, 'kindness, generosity, community', NOW() + INTERVAL '42 days'),
    ((SELECT id FROM auth_user WHERE username = 'robert_anderson'), 'Have a deep conversation', 'Go beyond small talk - discuss dreams, fears, and meaningful topics.', 'high', 'in_progress', TRUE, 'weekly', 1, 60, 'conversation, depth, connection', NOW() + INTERVAL '49 days'),
    ((SELECT id FROM auth_user WHERE username = 'robert_anderson'), 'Resolve a conflict or apologize', 'Address any tension in relationships with honesty and empathy.', 'high', 'in_progress', TRUE, 'weekly', 1, 30, 'conflict, resolution, growth', NOW() + INTERVAL '56 days'),
    ((SELECT id FROM auth_user WHERE username = 'robert_anderson'), 'Volunteer for a cause', 'Give your time to help others through a charity or community organization.', 'urgent', 'in_progress', TRUE, 'weekly', 1, 180, 'volunteering, community, giving', NOW() + INTERVAL '63 days'),
    ((SELECT id FROM auth_user WHERE username = 'robert_anderson'), 'Host a gathering or party', 'Bring people together by organizing a memorable event at your home.', 'urgent', 'in_progress', TRUE, 'monthly', 1, 240, 'hosting, party, social', NOW() + INTERVAL '70 days');

-- =============================================================================
-- TASKS - User 10: Lisa Thomas (Entrepreneur & Business)
-- =============================================================================

INSERT INTO tasks_task (user_id, title, description, priority, status, is_recurring, recurrence_period, recurrence_target_count, estimated_duration, tags, due_date) VALUES
    ((SELECT id FROM auth_user WHERE username = 'lisa_thomas'), 'Review key business metrics', 'Check dashboard for revenue, users, or other KPIs daily.', 'low', 'todo', TRUE, 'daily', 1, 10, 'metrics, analytics, business', NOW() + INTERVAL '7 days'),
    ((SELECT id FROM auth_user WHERE username = 'lisa_thomas'), 'Respond to customer inquiries', 'Provide excellent support by addressing customer questions promptly.', 'low', 'todo', TRUE, 'daily', 1, 30, 'customer, support, service', NOW() + INTERVAL '14 days'),
    ((SELECT id FROM auth_user WHERE username = 'lisa_thomas'), 'Create content for social media', 'Build brand presence with valuable posts on LinkedIn, Twitter, or Instagram.', 'medium', 'todo', TRUE, 'weekly', 3, 30, 'content, social-media, marketing', NOW() + INTERVAL '21 days'),
    ((SELECT id FROM auth_user WHERE username = 'lisa_thomas'), 'Network with other entrepreneurs', 'Attend startup events or schedule calls with fellow founders.', 'medium', 'todo', TRUE, 'weekly', 2, 60, 'networking, founders, community', NOW() + INTERVAL '28 days'),
    ((SELECT id FROM auth_user WHERE username = 'lisa_thomas'), 'Work on product improvements', 'Based on user feedback, enhance your product or service.', 'medium', 'todo', TRUE, 'weekly', 3, 120, 'product, improvement, development', NOW() + INTERVAL '35 days'),
    ((SELECT id FROM auth_user WHERE username = 'lisa_thomas'), 'Study competitors and market', 'Analyze what competitors are doing and identify market opportunities.', 'high', 'in_progress', TRUE, 'weekly', 1, 60, 'research, competitors, market', NOW() + INTERVAL '42 days'),
    ((SELECT id FROM auth_user WHERE username = 'lisa_thomas'), 'Reach out to potential customers', 'Cold outreach to leads through email, LinkedIn, or calls.', 'high', 'in_progress', TRUE, 'weekly', 5, 60, 'sales, outreach, growth', NOW() + INTERVAL '49 days'),
    ((SELECT id FROM auth_user WHERE username = 'lisa_thomas'), 'Write and send newsletter', 'Keep your audience engaged with valuable email content.', 'high', 'in_progress', TRUE, 'weekly', 1, 60, 'newsletter, email, marketing', NOW() + INTERVAL '56 days'),
    ((SELECT id FROM auth_user WHERE username = 'lisa_thomas'), 'Pitch to investors or partners', 'Present your business to potential investors or strategic partners.', 'urgent', 'in_progress', TRUE, 'weekly', 1, 90, 'pitch, investors, fundraising', NOW() + INTERVAL '63 days'),
    ((SELECT id FROM auth_user WHERE username = 'lisa_thomas'), 'Achieve monthly revenue target', 'Focus on sales and retention to hit your MRR or revenue goals.', 'urgent', 'in_progress', TRUE, 'weekly', 5, 120, 'revenue, goals, ambitious', NOW() + INTERVAL '70 days');

-- =============================================================================
-- TASK COMPLETIONS (sample completions for some tasks)
-- =============================================================================

-- Add completions for the first few tasks of each user
DO $$
DECLARE
    task_record RECORD;
    completion_count INTEGER;
BEGIN
    FOR task_record IN
        SELECT t.id, t.estimated_duration, ROW_NUMBER() OVER (PARTITION BY t.user_id ORDER BY t.id) as task_num
        FROM tasks_task t
    LOOP
        -- Only add completions for first 4 tasks per user
        IF task_record.task_num <= 4 THEN
            completion_count := LEAST(task_record.task_num, 3);
            FOR i IN 1..completion_count LOOP
                INSERT INTO tasks_taskcompletion (task_id, notes, duration_minutes, completed_at)
                VALUES (
                    task_record.id,
                    'Completed session ' || i,
                    task_record.estimated_duration,
                    NOW() - (i || ' days')::INTERVAL
                );
            END LOOP;
        END IF;
    END LOOP;
END $$;

-- =============================================================================
-- Summary
-- =============================================================================

DO $$
DECLARE
    user_count INTEGER;
    task_count INTEGER;
    completion_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO user_count FROM auth_user;
    SELECT COUNT(*) INTO task_count FROM tasks_task;
    SELECT COUNT(*) INTO completion_count FROM tasks_taskcompletion;

    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Seed data inserted successfully!';
    RAISE NOTICE 'Users: %', user_count;
    RAISE NOTICE 'Tasks: %', task_count;
    RAISE NOTICE 'Completions: %', completion_count;
    RAISE NOTICE '===========================================';
    RAISE NOTICE 'Login credentials for all users:';
    RAISE NOTICE 'Password: password123';
    RAISE NOTICE '===========================================';
END $$;

