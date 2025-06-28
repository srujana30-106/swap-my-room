# Swap My Room 

**Swap My Room** is a simple web application that I created specifically for my **hostel community** to make it easy for students to **swap their rooms with others based on mutual preferences**.  
After seeing how time-consuming and inefficient the manual process of finding someone to swap with was, I built this platform to streamline the process and help my fellow hostel mates.

---

## Purpose & My Intention

The main purpose of this project was to solve a **real, problem in my hostel**:

After room allotment, many students find their assigned rooms don’t suit their needs — whether it’s the block, floor, roommates. Meanwhile, someone else in the hostel might actually want that exact type of room.

My intention behind building **Swap My Room** was to:
- Provide a **dedicated platform for my hostel mates** to list their current rooms and mention what kind of swap they’re looking for.
- Replace the informal, time-consuming process of finding a swap partner through word of mouth or random notices.
- Apply my skills to build a **practical full-stack web application**, enhancing my knowledge of Flask, PostgreSQL, and deploying real-world projects.

---

## Features

**Post Your Current Room**  
- Students can submit details about their allotted rooms: block, floor, roommates, facilities, etc.

**Specify Desired Swap Preferences**  
- Clearly state the kind of room or location they’d prefer to move into.

**Browse Other Listings**  
- See rooms posted by other hostel mates and use filters to find the best match.

**Request a Swap via WhatsApp or Phone**  
- The app generates a direct WhatsApp link so students can easily connect and discuss swaps.

**Authentication & Profiles**  
- Secure login system to manage your room posts, preferences, and incoming swap requests.

**Basic Admin Dashboard**  
- To oversee users, room listings, and monitor activity.

---

## Tech Stack

- **Backend:** Python, Flask
- **Database:** PostgreSQL (deployed on Render)
- **Frontend:** HTML, CSS, Jinja2 templates
- **ORM:** SQLAlchemy

---

##  How to Set Up & Run Locally

**Clone the repository**
```bash
git clone https://github.com/yourusername/swap-my-room.git
cd swap-my-room
```

**Create a virtual environment & activate it**
```bash
python -m venv venv
source venv/bin/activate     # On Windows: venv\Scripts\activate
```

**Install dependencies**
```bash
pip install -r requirements.txt
```

**Add your configuration**

Create a `config.py` file (or set these as environment variables) with:

```python
DATABASE_URL = "postgresql://username:password@host:port/dbname"
SECRET_KEY = "your_secret_key"

MAIL_SERVER = "smtp.yourprovider.com"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = "your_email"
MAIL_PASSWORD = "your_password"
```

**Run the application**
```bash
flask run
```
Then open `http://127.0.0.1:5000` in your browser.

---

## Database Overview

- **users** — stores student login details & profiles.
- **rooms** — stores posted room information.
- **swap_requests** — tracks who requested swaps and their statuses.

---

## Future Plans & Ideas

Integrate **live chat** so students can negotiate swap details instantly.  
Add **hostel block maps** to visualize where available rooms are.  

---

## Why I Built This

I developed **Swap My Room** to directly help students in my hostel:

- To reduce the hassle of manually finding someone to swap rooms with.
- To provide a **transparent, structured way** to post, search, and request swaps.
- As a hands-on learning project to implement a **complete web application**, from backend to frontend, and deploy it live.

It’s a project close to my heart because it directly solves a **problem faced by me and my friends** in our hostel.

---

## Contact

Feel free to reach out to me if you’d like to discuss improvements, see the deployment, or collaborate:

- **Email:** (sanakalakshmisrujana@gmail.com)
- **GitHub:** [srujana30-106](https://github.com/srujana30-106)

---

## Show Your Support

If you found this project interesting or useful, please ⭐ the repository — it helps more people discover it and keeps me motivated to build more solutions like this!

---
