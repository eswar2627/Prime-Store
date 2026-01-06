**Prime Store – Full-Stack E-Commerce Web Application**

Prime Store is a production-ready, full-stack e-commerce platform built using Django.
It includes user authentication, cart and checkout flow, Stripe payment gateway integration, order history, and a full admin analytics dashboard with sales, customers, and inventory insights.

**User Features**

1. Authentication

   User registration and login

   Secure session-based authentication

   Password hashing and validation

2. Cart Management

   Add, update, and remove products

   Session-based cart for guest users

   Auto-calculated totals and quantity management

3. Stripe Payment Gateway Integration

   Secure checkout via Stripe

   Payment success/failure handling

   Automatic order creation after successful payment

4. Checkout & Address Management

   Add and manage delivery addresses

   Address selection during checkout

   Order summary preview before payment

5. Product Browsing & Details

   Product listings with filters

   Individual product detail pages


6. Order History

   View all past orders

   Payment status, delivery details, item breakdown

**Admin Features (Advanced E-Commerce Dashboard)**

7. Top Selling Products


8. Daily Sales Chart + Top Selling Products Chart


9. Low Stock Alerts

  

10. Monthly New Customers & Top Customers

  

11. Monthly Sales & Recent Orders

    Monthly revenue dashboard


12. Payment Status Breakdown & Customer Type Breakdown

    New vs Returning customers

13. Store Analytics

    Revenue, sales, growth trends

    Inventory consumption

    Customer behavior metrics

**Tech Stack**

**Backend**

Python

Django

Django ORM

Stripe API


**Frontend**


HTML5, CSS3, Bootstrap

JavaScript

AJAX interactions


**Database**

PostgreSQL


**Tools & Others**


Git & GitHub


**Virtual environment**


dotenv for environment variables

Django Admin customization

<img width="1920" height="952" alt="login" src="https://github.com/user-attachments/assets/72637ade-6ff3-4f59-b200-e257aab025ab" />
<img width="1894" height="955" alt="register" src="https://github.com/user-attachments/assets/0ce78fcb-f2fe-4439-8a6a-90beb49928df" />
<img width="1890" height="932" alt="Screenshot (1050)" src="https://github.com/user-attachments/assets/7a27b882-9110-4892-8e89-57fd6d196d05" />
<img width="1920" height="957" alt="product details" src="https://github.com/user-attachments/assets/a9f337e0-15b2-4a29-b42c-df16ee4e30c4" />
<img width="1920" height="954" alt="cart" src="https://github.com/user-attachments/assets/5ed8cc80-f18f-45d1-a0d9-cd7c3db09d8f" />
<img width="1920" height="952" alt="check out" src="https://github.com/user-attachments/assets/634bac41-cb83-4a73-8241-46555099c069" />
<img width="1920" height="958" alt="stripe payment gateway" src="https://github.com/user-attachments/assets/c13f82f8-88fc-4115-a054-6d8fd82ad696" />
<img width="1901" height="955" alt="order history" src="https://github.com/user-attachments/assets/5bd9a2bd-fb45-40da-8905-df42ff570851" />
<img width="1896" height="941" alt="Admin Dashboard and Top Selling Products" src="https://github.com/user-attachments/assets/2ed77459-525c-4495-8c21-8c915f0b1f8d" />
<img width="1900" height="957" alt="Daily Sales and Top Selling Products chart" src="https://github.com/user-attachments/assets/388f6665-7636-4a1a-8076-0ae8b3a48d70" />
<img width="1900" height="951" alt="Payment Status Breakdown and Customer Typee Breakdown" src="https://github.com/user-attachments/assets/b8968344-45d1-471b-843d-fb01626d1bab" />
<img width="1894" height="749" alt="Monthly New Customers and Top Customers" src="https://github.com/user-attachments/assets/df160550-1f84-465e-a033-231f16abf450" />
<img width="1894" height="960" alt="monthly sales and Recent Orders" src="https://github.com/user-attachments/assets/639f43ff-ea28-400c-87e2-56fdf7df23fc" />
<img width="1894" height="230" alt="Low Stock Alert" src="https://github.com/user-attachments/assets/bd6747e8-714e-435c-b1d0-318d9e92e969" />
<img width="1920" height="955" alt="Store Analytics" src="https://github.com/user-attachments/assets/985a579c-f96e-4ddd-912a-a640e18d44e7" />


**How to Run the Project Locally**

**1. Clone the repository**

     git clone https://github.com/your-username/prime-store.git
     
     cd prime-store


**2. Create a virtual environment**

     python -m venv venv
     
     venv\Scripts\activate   (Windows)
     
     source venv/bin/activate (Linux/Mac)


**3. Install dependencies**

      pip install -r requirements.txt

**4. Add environment variables**

     Create a .env file:

     SECRET_KEY=your_secret_key
     
     STRIPE_PUBLIC_KEY=your_key

     STRIPE_SECRET_KEY=your_key

     DATABASE_URL=your_database_url


**5. Run migrations**

     python manage.py migrate


**6. Start the server**

     python manage.py runserver

**Future Enhancements**

     Product reviews and ratings

     Search autocomplete

     Coupon system

     Delivery tracking integration


** Author**

  **Eswar Maguluri**

  Full-Stack Developer

  Open to remote roles, freelance projects, and collaborations.
