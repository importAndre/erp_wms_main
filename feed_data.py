import requests
import random
import time


URL = "http://127.0.0.1:8003"

TOKEN = None


def login():
    global TOKEN

    url = f"{URL}/users/login"
    payload = {
        "email": "test123@test.com",
        "password": "test"
    }
    req = requests.post(url=url, json=payload)
    TOKEN = req.json()['access_token']



def generate_users(x = 10):
    url = f"{URL}/users/create"
    start_time = time.localtime()
    s = time.mktime(start_time)
    for _ in range(x):
        n = random.randint(0, x**2)
        payload = {
        "username": "Test",
        "email": f"test{n}@test.com",
        "is_superuser": True,
        "is_employee": False,
        "password": "test"
        }
        requests.post(url=url, json=payload)
    
    end_time = time.localtime()
    e = time.mktime(end_time)
    final_time = e - s
    print(f"Time for create {x} users: {final_time} seconds")


def generate_products(x = 100, headers=None):
    url = f"{URL}/products/create"
    start_time = time.localtime()
    s = time.mktime(start_time)


    for _ in range(x):
        n = random.randint(0, x**2)
        payload = {
            "company_id": 1,
            "sku": f"test{n}",
            "name": f"Product Test {n}",
        }
        requests.post(url=url, json=payload, headers=headers)
    
    end_time = time.localtime()
    e = time.mktime(end_time)
    final_time = e - s
    print(f"Time for create {x} products: {final_time} seconds")
    

def get_products(headers = None):
    url = f"{URL}/products"
    start_time = time.localtime()
    s = time.mktime(start_time)

    req = requests.get(url=url, headers=headers)

    end_time = time.localtime()
    e = time.mktime(end_time)
    final_time = e - s
    data =  req.json()
    print(f"Time for get {len(data)} products: {final_time} seconds")
    return data

def generate_compositions(x=10, headers=None):
    url = f"{URL}/compositions"
    add_item_url = f"{URL}/compositions/add-item"
    start_time = time.localtime()

    products = get_products(headers=headers)

    for i in range(x):
        n = random.randint(0, x**2)
        payload = {
            "company_id": 1,
            "sku": f"comp{n}",
            "name": f"composition {n}"
        }
        req = requests.post(url=url, headers=headers, json=payload)
        if req:
            data = req.json()
            comp_id = data['id']

            item_payload = {
                "composition_id": comp_id,
                "product_id": products[i]['id'],
                "amount_required": n
            }





if __name__ == "__main__":
    login()
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    # generate_users()
    generate_products(headers=headers, x=8696)
    products = get_products(headers=headers)
