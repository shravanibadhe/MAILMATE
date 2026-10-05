"""Builds email_dataset.csv - a labelled synthetic email dataset for MailMate.
Each row: id, subject, email, intent, sentiment, urgent, sender, date, time, reference, level
level = 'standard' (clear keywords) or 'hard' (indirect wording / mixed signals)."""
import csv, random
random.seed(42)
NAMES=["Priya Sharma","Rahul Mehta","Amit Patil","Neha Verma","Sanjay Rao","Kavita Nair","Ankit Desai","Meera Iyer","Vikram Singh","Sneha Joshi","Farhan Sheikh","Anita Deshmukh","Deepak Kulkarni","Ritu Kapoor","Manoj Pawar","Tanvi Shah","Arjun Reddy","Pooja Kulkarni","Karan Malhotra","Divya Menon"]
DAYS=["Monday","Tuesday","Wednesday","Thursday","Friday","12 October","5 November","20 November","3 December","15 January"]
TIMES=["10 am","11 am","2 pm","3 pm","4 pm","5 pm"]
SIGN=["Regards","Thanks","Best","Cheers","Sincerely"]
GREET=["Hi,","Hello,","Dear Sir/Madam,","Hi team,","Good morning,"]
rows=[]
def add(subject,body,intent,sent="neutral",urg=False,date="",time="",ref="",level="standard"):
    name=random.choice(NAMES); g=random.choice(GREET)
    email=f"{g}\n\n{body}\n\n{random.choice(SIGN)}\n{name}"
    rows.append([len(rows)+1,subject,email,intent,sent,"yes" if urg else "no",name,date,time,ref,level])
def D(): return random.choice(DAYS)
def T(): return random.choice(TIMES)
def R(p): return f"{p}{random.randint(10000,99999)}"

M=[("Can we schedule a meeting on {d} at {t} to discuss the project?"),
 ("I would like to set up a call on {d} at {t} with the design team."),
 ("Are you available for a quick sync on {d} at {t}?"),
 ("Please let me know if we can meet on {d} at {t} to discuss the launch plan."),
 ("I need to reschedule our meeting planned for {d}. Can we do {t} instead?")]
I=[("We would like to invite you for an interview for the Software Engineer position on {d} at {t}. Please confirm your availability."),
 ("Your interview with our hiring team is scheduled for {d} at {t}. Kindly confirm."),
 ("Thank you for applying. We would like to take the next round of interview on {d} at {t}."),
 ("The candidate interview for the analyst role is planned on {d} at {t}. Are you available?")]
L=[("I would like to request leave from {d} to {d2} due to a family function."),
 ("I am not feeling well and need sick leave on {d} and {d2}."),
 ("Please approve my vacation leave starting {d}. I will complete my pending work before that."),
 ("I need a day off on {d} for a personal matter. Kindly grant leave.")]
C=[("My order {r} arrived damaged and I need a refund. I am very disappointed."),
 ("This is the worst service. The product is broken and nobody has fixed the problem."),
 ("I have a complaint about the delay. The issue has not been solved for three days and this is unacceptable."),
 ("The device stopped working after two days. I want a refund. This is a terrible experience.")]
P=[("Please find attached invoice {r} for Rs. {a}. Payment is due by {d}."),
 ("This is a reminder that your bill of ${a} is due on {d}. Kindly complete the payment."),
 ("We have not received the payment for invoice {r}. Please pay at the earliest."),
 ("I have made the payment of Rs. {a} for invoice {r}. Please share the receipt.")]
O=[("I placed an order {r} last week and it has not been delivered yet. Can you tell me the shipping status?"),
 ("Could you please share the tracking details for my order {r}? The package has not arrived."),
 ("My order {r} was supposed to be delivered on {d}. Please update me on the delivery."),
 ("I want to track my shipment for order {r}.")]
A=[("I am writing to apply for the marketing executive vacancy. Please find my resume attached."),
 ("I would like to apply for the data analyst job. My CV is attached for your review."),
 ("I am interested in the open position of web developer and have attached my resume."),
 ("Please consider my application for the content writer vacancy. My CV is enclosed.")]
E=[("You are invited to our annual conference on {d} at {t}. Please RSVP."),
 ("We are hosting a webinar on data privacy on {d} at {t}. We would love for you to join. Kindly RSVP."),
 ("Join us for the company party on {d} at {t}. Please confirm your attendance with an RSVP."),
 ("We invite you to our workshop on cloud computing on {d} at {t}. RSVP by next week.")]
TH=[("Thank you so much for your help with the project. I really appreciate it."),
 ("Thanks for the quick support yesterday. I am grateful for your time."),
 ("I appreciate the guidance you gave me. Thank you again."),
 ("Many thanks for sending the notes. I truly appreciate your effort.")]
G=[("Do you know when the new office will be ready? Let me know when you can."),
 ("Are you free to help me with something? It is about the report."),
 ("Could you share the updated project notes when possible?"),
 ("Just checking if the shared folder is working for everyone."),
 ("What is the plan for next week's work?")]

def gen(intent,tmpls,n,sent="neutral",urg_p=0.0,pos=False,uses=("d","t","r","a"),subj=""):
    for k in range(n):
        tpl=tmpls[k%len(tmpls)]
        d,d2,t,r,a=D(),D(),T(),R({"order":"#ORD","payment":"INV-","complaint":"#AB"}.get(intent,"#X")),random.choice(["12,000","45,000","1,200","8,500"])
        body=tpl.format(d=d,d2=d2,t=t,r=r,a=a)
        urg=random.random()<urg_p
        if urg: body+=random.choice([" This is urgent."," Please reply ASAP."," I need this resolved immediately."])
        s=sent
        add(subj,body,intent,s,urg,d if "{d}" in tpl else "",t if "{t}" in tpl else "",r if "{r}" in tpl else "")
gen("meeting",M,20,subj="Meeting request")
gen("interview",I,20,subj="Interview invitation")
gen("leave",L,20,subj="Leave request")
gen("complaint",C,20,sent="negative",urg_p=0.6,subj="Complaint")
gen("payment",P,20,subj="Payment")
gen("order",O,20,subj="Order status")
gen("application",A,20,subj="Job application")
gen("event",E,20,sent="neutral",subj="Invitation")
gen("thanks",TH,20,sent="positive",subj="Thank you")
gen("general",G,20,subj="Quick question")
# fix sentiment for non-keyword cases is left as generated; sentiment truth computed below by hand-labelled rules per intent
# ---- hand-written HARD cases (indirect wording, no obvious keyword, or mixed signals) ----
H=[
("Can we catch up on Thursday at 4 pm?","meeting","neutral",False,"Thursday","4 pm",""),
("Let's talk about the budget on Monday at 11 am.","meeting","neutral",False,"Monday","11 am",""),
("I will be away from 12 October to 14 October. Please manage my tasks.","leave","neutral",False,"12 October","",""),
("I won't be in office tomorrow because I have a fever.","leave","neutral",False,"","",""),
("The parcel never showed up even though the site said delivered. Order #ORD55123.","order","negative",False,"","","ORD55123"),
("Where is my package? Order #ORD77001 should have come on Friday.","order","neutral",False,"Friday","","ORD77001"),
("Your account was charged twice for invoice INV-33012. Please check the transaction.","payment","negative",False,"","","INV-33012"),
("We will pay the outstanding amount of Rs. 20,000 by 15 January.","payment","neutral",False,"15 January","",""),
("The app keeps crashing and I am frustrated. This is not working at all, please fix it urgently.","complaint","negative",True,"","",""),
("I am extremely unhappy with how my case was handled. This delay is not acceptable.","complaint","negative",False,"","",""),
("Please find my profile attached for the open role of Java developer.","application","neutral",False,"","",""),
("Looking for opportunities in your design team. Resume attached.","application","neutral",False,"","",""),
("Hope to see you at the annual day function on 3 December at 5 pm. Please let us know if you can come.","event","neutral",False,"3 December","5 pm",""),
("You are cordially invited to the launch party on Friday at 3 pm.","event","neutral",False,"Friday","3 pm",""),
("It was great working with you. Thanks a lot!","thanks","positive",False,"","",""),
("Really grateful for your support during the audit.","thanks","positive",False,"","",""),
("Is the printer on the third floor working?","general","neutral",False,"","",""),
("Please share the slides from yesterday.","general","neutral",False,"","",""),
("Do we have a holiday on Friday?","general","neutral",False,"Friday","",""),
("Could you confirm if you received the files?","general","neutral",False,"","",""),
("Interview round two is on 20 November at 10 am. Please be ready with your portfolio.","interview","neutral",False,"20 November","10 am",""),
("We shortlisted you for the position and want to talk to you on Tuesday at 2 pm.","interview","neutral",False,"Tuesday","2 pm",""),
("Need to discuss the invoice problem on a call tomorrow.","meeting","neutral",False,"","",""),
("The product was great but delivery was late and the packaging was damaged. I want a refund.","complaint","negative",False,"","",""),
("Thanks, but my order #ORD88220 is still missing and I am disappointed.","order","negative",False,"","","ORD88220"),
("Kindly clear the pending bill of Rs. 8,500 due on Wednesday.","payment","neutral",False,"Wednesday","",""),
("Sorry I cannot attend the meeting on Monday at 10 am. Can we move it?","meeting","neutral",False,"Monday","10 am",""),
("I am writing to apply for leave next week as well as submit my project.","leave","neutral",False,"","",""),
("Heartfelt thanks for the invitation to the conference.","thanks","positive",False,"","",""),
("Join our free workshop next week. Register using the link below.","event","neutral",False,"","",""),
]
for s,intent,sent,urg,d,t,r in H:
    add("(hard case)",s,intent,sent,urg,d,t,r,"hard"); rows[-1][-1]="hard"
# sentiment ground truth for standard rows: complaints negative, thanks/event positive, others neutral (+ urgent flag as generated)
random.shuffle(rows)
for i,r in enumerate(rows,1): r[0]=i
with open("email_dataset.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["id","subject","email","intent","sentiment","urgent","sender","date","time","reference","level"]); w.writerows(rows)
print(len(rows),"rows written")
