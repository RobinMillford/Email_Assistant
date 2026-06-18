"""
test_scenarios.py — 10 evaluation scenarios with human-reference emails.

Each scenario contains:
  - id            : unique identifier
  - name          : short descriptive label
  - intent        : the core purpose of the email
  - key_facts     : list of facts that MUST appear in the generated email
  - tone          : desired style descriptor
  - human_reference : ideal email written by a human expert (the benchmark)
"""

SCENARIOS = [
    # ------------------------------------------------------------------
    # 1. Job Interview Follow-up
    # ------------------------------------------------------------------
    {
        "id": 1,
        "name": "Job Interview Follow-up",
        "intent": "Send a thank-you and follow-up email after a job interview",
        "key_facts": [
            "Interview was for the Senior Data Engineer role at NeuralBridge",
            "Panel included hiring manager Sarah Chen and tech lead Marcus Rivera",
            "Interview took place yesterday afternoon",
            "Candidate discussed experience with Apache Spark and real-time pipelines",
            "Final hiring decision expected within two weeks",
        ],
        "tone": "Formal, enthusiastic, and professional",
        "human_reference": """\
Subject: Thank You — Senior Data Engineer Interview (Yesterday)

Dear Sarah and Marcus,

Thank you both for taking the time to meet with me yesterday afternoon. It was a pleasure to learn more about the Senior Data Engineer role at NeuralBridge and to share my experience firsthand.

I particularly enjoyed our conversation around real-time data pipelines and the opportunity to discuss my work with Apache Spark in depth. The challenges you outlined resonated strongly with projects I have tackled, and I left the interview even more enthusiastic about the team's direction.

I am very excited about the possibility of joining NeuralBridge and contributing to the work you are doing. I understand that a final decision is expected within two weeks and I will look forward to hearing from you.

Please do not hesitate to reach out should you need any additional information in the meantime.

Sincerely,
[Your Name]
""",
    },

    # ------------------------------------------------------------------
    # 2. Project Delay Notification
    # ------------------------------------------------------------------
    {
        "id": 2,
        "name": "Project Delay Notification",
        "intent": "Inform the client about a delay in project delivery",
        "key_facts": [
            "Project is the 'Phoenix Dashboard' for Vertex Analytics",
            "Original launch date was this Friday",
            "A critical API integration bug was discovered during QA testing",
            "New estimated delivery date is next Thursday",
            "Daily status updates will be sent from tomorrow",
            "No additional cost will be charged for the delay",
        ],
        "tone": "Apologetic, transparent, and professional",
        "human_reference": """\
Subject: Important Update: Phoenix Dashboard Delivery — Revised Timeline

Dear [Client Name],

I am writing to inform you of an unforeseen delay affecting the delivery of the Phoenix Dashboard for Vertex Analytics, which was originally scheduled for launch this Friday.

During final-stage quality assurance testing, our engineering team identified a critical bug within one of the API integrations. Rather than deliver a compromised product, we made the decision to resolve this issue correctly before handover.

Our revised estimated delivery date is next Thursday. To keep you fully informed throughout this period, we will begin sending daily status updates from tomorrow morning covering progress, any new findings, and our resolution steps.

I want to assure you that this delay will carry no additional cost to your project. We sincerely apologise for the disruption and appreciate your patience and understanding. Please do not hesitate to contact me directly if you have any questions or concerns.

Yours sincerely,
[Your Name]
""",
    },

    # ------------------------------------------------------------------
    # 3. Partnership Cold Outreach
    # ------------------------------------------------------------------
    {
        "id": 3,
        "name": "Partnership Cold Outreach",
        "intent": "Reach out to a potential business partner for a strategic collaboration",
        "key_facts": [
            "Target company is GreenLoop Energy, a leader in sustainable logistics",
            "Proposing a co-branded carbon-offset tracking platform",
            "Sender's company is DataGreen Tech, specialising in ESG analytics",
            "Identified GreenLoop's VP of Partnerships, James Holloway, as the recipient",
            "Requesting a 20-minute exploratory call in the next two weeks",
        ],
        "tone": "Confident, concise, and persuasive",
        "human_reference": """\
Subject: Partnership Opportunity — DataGreen × GreenLoop Carbon-Offset Platform

Dear James,

I am reaching out because I believe GreenLoop Energy and DataGreen Tech are exceptionally well-positioned to build something valuable together.

At DataGreen, we specialise in ESG analytics and data infrastructure for sustainability-focused organisations. Having followed GreenLoop's leadership in sustainable logistics, I see a compelling opportunity to develop a co-branded carbon-offset tracking platform — one that would offer your clients real-time, auditable emissions data while extending DataGreen's capabilities into the logistics sector.

I would love to explore this further with you in a focused 20-minute call over the next two weeks. Would you have availability to connect?

Best regards,
[Your Name]
DataGreen Tech
""",
    },

    # ------------------------------------------------------------------
    # 4. Meeting Reschedule Request
    # ------------------------------------------------------------------
    {
        "id": 4,
        "name": "Meeting Reschedule Request",
        "intent": "Request to reschedule an upcoming team meeting",
        "key_facts": [
            "Meeting was scheduled for Tuesday at 3 PM",
            "Sender has a conflicting external client call that cannot be moved",
            "Proposing Wednesday at 2 PM or Thursday at 11 AM as alternatives",
            "The original agenda — sprint retrospective review — will remain unchanged",
            "Recipient is the direct manager, Priya Nair",
        ],
        "tone": "Casual, friendly, and considerate",
        "human_reference": """\
Subject: Quick Reschedule Request — Tuesday's Sprint Retrospective

Hi Priya,

Hope you're having a good week! I wanted to flag a scheduling conflict on my end — I have an external client call on Tuesday at 3 PM that I'm unable to move, which unfortunately clashes with our sprint retrospective.

Would it be possible to shift the meeting? I have two slots that could work on my side: Wednesday at 2 PM or Thursday at 11 AM. Happy to go with whichever suits the rest of the team better — the agenda will stay exactly the same either way.

Let me know what works best and I'll send over an updated invite straight away. Sorry for the short notice!

Thanks,
[Your Name]
""",
    },

    # ------------------------------------------------------------------
    # 5. Customer Complaint Resolution
    # ------------------------------------------------------------------
    {
        "id": 5,
        "name": "Customer Complaint Resolution",
        "intent": "Respond to a customer complaint about a delayed shipment",
        "key_facts": [
            "Customer is Amara Osei, order number TRK-8821",
            "Order was delayed by 6 days due to a regional carrier disruption",
            "The package was delivered this morning",
            "Offering a 20% discount on the customer's next order as goodwill",
            "Customer support line is open 9 AM – 6 PM Monday to Friday",
        ],
        "tone": "Empathetic, sincere, and solution-focused",
        "human_reference": """\
Subject: Resolution for Your Order TRK-8821 — Our Sincere Apologies

Dear Amara,

Thank you for contacting us, and I want to begin by sincerely apologising for the delay to your order TRK-8821. I completely understand how frustrating an unexpected wait can be, and I am sorry for the inconvenience this has caused.

The delay was the result of a regional carrier disruption that impacted a number of shipments in your area. I am pleased to confirm, however, that your package was delivered earlier this morning.

As a token of our apology, we would like to offer you a 20% discount on your next order with us. This will be applied automatically at checkout and reflects our genuine appreciation for your patience and understanding.

Should you have any further questions or concerns, our customer support team is available Monday to Friday, 9 AM to 6 PM and would be happy to assist.

With sincere apologies and warm regards,
[Your Name]
Customer Experience Team
""",
    },

    # ------------------------------------------------------------------
    # 6. Business Proposal Submission
    # ------------------------------------------------------------------
    {
        "id": 6,
        "name": "Business Proposal Submission",
        "intent": "Submit a formal business proposal for a software development contract",
        "key_facts": [
            "Proposal is for a custom inventory management system for Orion Retail Group",
            "Sender's firm is Apex Dev Solutions",
            "Project estimated at £85,000 with a 14-week delivery timeline",
            "The attached proposal PDF contains technical specifications and phased milestones",
            "Post-launch includes 6 months of complimentary technical support",
            "Request for a formal review meeting within the next 10 business days",
        ],
        "tone": "Formal and confident",
        "human_reference": """\
Subject: Formal Proposal — Custom Inventory Management System | Apex Dev Solutions

Dear [Recipient Name],

Please find attached Apex Dev Solutions' formal proposal for the design and development of a custom inventory management system for Orion Retail Group.

We have approached this project with a thorough understanding of your operational requirements. Our proposed solution carries an investment of £85,000, with an estimated delivery timeline of 14 weeks. The attached proposal document contains full technical specifications, our phased project milestones, and the associated deliverables for each stage.

As an expression of our long-term commitment to this engagement, the proposal also includes six months of complimentary technical support following launch, ensuring a smooth transition and continued system performance.

We are confident that Apex Dev Solutions is the right partner to deliver this project on time and to the standard Orion Retail Group expects. We would welcome the opportunity to discuss the proposal in a formal review meeting within the next 10 business days at a time of your convenience.

I look forward to your response.

Yours sincerely,
[Your Name]
Apex Dev Solutions
""",
    },

    # ------------------------------------------------------------------
    # 7. Team Wellness Programme Announcement
    # ------------------------------------------------------------------
    {
        "id": 7,
        "name": "Team Wellness Programme Announcement",
        "intent": "Announce a new employee wellness programme to the entire team",
        "key_facts": [
            "Programme is called 'Thrive@Work', launching on the 1st of next month",
            "Includes mental health support, weekly yoga sessions, and nutrition workshops",
            "All sessions are voluntary and held during lunch hours",
            "Partnered with WellnessFirst, a certified wellbeing provider",
            "Staff can register via the internal HR portal by end of this week",
        ],
        "tone": "Enthusiastic, inclusive, and warm",
        "human_reference": """\
Subject: Introducing Thrive@Work — Your New Workplace Wellness Programme!

Hi Team,

We are so excited to announce the launch of Thrive@Work, our new employee wellness programme, kicking off on the 1st of next month!

Developed in partnership with WellnessFirst, a certified wellbeing provider, Thrive@Work has been designed with every member of our team in mind. The programme includes dedicated mental health support, weekly yoga sessions, and interactive nutrition workshops — all held during lunch hours so they fit around your day.

Every session is completely voluntary — this is all about giving you options to support your wellbeing in whatever way resonates most. There is no pressure, just an open invitation to take care of yourself.

To register your interest and secure your spot, head to the internal HR portal by end of this week.

We truly believe a healthy team is a happy team, and we cannot wait to kick this off together. See you at Thrive@Work!

Warmly,
[Your Name]
People & Culture Team
""",
    },

    # ------------------------------------------------------------------
    # 8. Recommendation Letter Request
    # ------------------------------------------------------------------
    {
        "id": 8,
        "name": "Recommendation Letter Request",
        "intent": "Request a professional letter of recommendation from a former supervisor",
        "key_facts": [
            "Requesting a recommendation from Dr. Helen Marsh, former PhD supervisor",
            "Application is for the MSc in Artificial Intelligence at TU Berlin",
            "Application deadline is 15 August",
            "Will attach a copy of the personal statement and CV for reference",
            "Open to discussing specific experiences Dr. Marsh could highlight",
            "Extremely grateful for any support she can provide",
        ],
        "tone": "Respectful, formal, and genuinely grateful",
        "human_reference": """\
Subject: Request for Letter of Recommendation — MSc AI Application, TU Berlin

Dear Dr. Marsh,

I hope this message finds you well. I am writing to ask whether you would be willing to provide a letter of recommendation in support of my application for the MSc in Artificial Intelligence programme at TU Berlin.

Having had the privilege of working under your supervision during my PhD, I believe your perspective on my research capabilities and academic development would carry significant value for the admissions committee. The application deadline is 15 August, and I want to ensure you have ample time should you agree.

To assist with the letter, I will attach a copy of my personal statement and CV for your reference. I am also very happy to arrange a brief call if it would be helpful to discuss any specific experiences or qualities you might wish to highlight.

I am incredibly grateful for the mentorship and guidance you have provided throughout my academic journey, and I truly appreciate any support you are able to offer with this next step.

Thank you sincerely for your time and consideration.

Yours respectfully,
[Your Name]
""",
    },

    # ------------------------------------------------------------------
    # 9. Overdue Invoice Payment Reminder
    # ------------------------------------------------------------------
    {
        "id": 9,
        "name": "Overdue Invoice Payment Reminder",
        "intent": "Send a firm reminder for an overdue invoice payment",
        "key_facts": [
            "Invoice number INV-2024-447 for £12,400",
            "Payment was due on 30 April — now 21 days overdue",
            "Client is Meridian Consulting Group",
            "Payment can be made via bank transfer using the details on the original invoice",
            "If payment is not received within 7 days, late payment charges may apply per contract terms",
            "Contact is accounts@yourdomain.com for any queries",
        ],
        "tone": "Professional, firm, and polite",
        "human_reference": """\
Subject: Payment Reminder — Invoice INV-2024-447 (21 Days Overdue) | £12,400

Dear [Accounts Contact],

I am writing to bring to your attention that Invoice INV-2024-447, issued to Meridian Consulting Group for the amount of £12,400, remains outstanding as of today. The payment due date was 30 April, meaning the invoice is now 21 days past due.

We kindly request that payment be arranged at your earliest convenience. Full payment details can be found on the original invoice, and bank transfer remains our preferred method of settlement.

Please be advised that should payment not be received within the next 7 days, late payment charges may become applicable in accordance with our agreed contract terms.

If there is a query regarding this invoice, or if you are experiencing any difficulty, please do not hesitate to contact our accounts team directly at accounts@yourdomain.com and we will be happy to assist.

We trust this matter will be resolved promptly and look forward to your confirmation of payment.

Yours sincerely,
[Your Name]
Accounts Receivable
""",
    },

    # ------------------------------------------------------------------
    # 10. New Client Welcome & Onboarding
    # ------------------------------------------------------------------
    {
        "id": 10,
        "name": "New Client Welcome & Onboarding",
        "intent": "Welcome a new client and provide onboarding details",
        "key_facts": [
            "New client is Luminary Digital, primary contact is Sophie Hartmann",
            "Dedicated account manager is Raj Patel",
            "Welcome onboarding call is booked for Monday at 10 AM",
            "Platform login credentials have been sent to Sophie's registered email",
            "A quick-start guide is attached to this email",
            "Support is available 24/7 via the live chat on the platform",
        ],
        "tone": "Warm, welcoming, and professional",
        "human_reference": """\
Subject: Welcome to the Platform, Luminary Digital! — Onboarding Details Inside

Dear Sophie,

Welcome, and congratulations on joining us — we are absolutely delighted to have Luminary Digital on board!

Your dedicated account manager, Raj Patel, will be your primary point of contact from here and will be guiding you through everything you need. He is looking forward to connecting with you on your onboarding call, which is booked for this Monday at 10 AM.

To help you hit the ground running, your platform login credentials have been sent to your registered email address. You will also find a quick-start guide attached to this email — it is a concise walkthrough of the key features to get you oriented quickly.

If you need anything before Monday or have questions at any point, our support team is available 24/7 via the live chat feature directly on the platform.

We are excited to be part of your journey. Welcome aboard!

Warmly,
[Your Name]
Client Success Team
""",
    },
]
