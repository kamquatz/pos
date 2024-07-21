import sqlite3, hashlib, os, uuid, psycopg2
from flask import current_app
from flask_login import current_user
from dotenv import load_dotenv

from utils.entities import Company, Package, Shop, ShopType, User

class Db():
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # Access the environment variables
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        db_port = os.getenv('DB_PORT')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        try:
            self.conn = psycopg2.connect(host=db_host, database=db_name, port=db_port, user=db_user, password=db_password)  
            
        except Exception as e:
            print(f'An error occurred: {e}')

        # # Initialize pos.db database or create if it does not exist.
        # db = 'pos.db'
        # self.conn = sqlite3.connect(db)
        # try:
        #     print(current_user.shop_id)
        #     db_2 = f'pos_{current_user.shop_id}.db'
        #     self.conn_2 = sqlite3.connect(db)
        # except Exception as e:
        #     self.conn_2 = None
          
    def hash_password(self, password):
        password_bytes = password.encode('utf-8')
        hash_object = hashlib.sha256(password_bytes)
        return hash_object.hexdigest()
    
    def create_base_tables(self):
        # Creates new tables in the pos.db database if they do not already exist.
        with current_app.open_resource("pos.sql") as f:
            cursor = self.conn.cursor()
            cursor.executescript(f.read().decode("utf8"))
        self.conn.commit()
        self.conn.close()
    
    def fetch_shop_types(self): 
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, description FROM shop_types")
        data = cursor.fetchall()
        self.conn.close()
        shop_types = []
        for shop_type in data:
            shop_types.append(ShopType(shop_type[0], shop_type[1], shop_type[2]))
            
        return shop_types    
    
    def get_user_by_id(self, id):
        cursor = self.conn.cursor()
        query = """
        SELECT id, name, phone, user_level_id, shop_id
        FROM users 
        WHERE id = ? 
        """
        cursor.execute(query, (id,))
        data = cursor.fetchone()
        self.conn.close()
        if data:
            return User(data[0], data[1], data[2], data[3], data[4])
        else:
            return None      
    
    def get_user_by_phone(self, phone):
        cursor = self.conn.cursor()
        query = """
        SELECT id, name, phone, user_level_id, shop_id
        FROM users 
        WHERE phone = ? 
        """
        cursor.execute(query, (phone,))
        data = cursor.fetchone()
        self.conn.close()
        if data:
            return User(data[0], data[1], data[2], data[3], data[4])
        else:
            return None    
           
    def authenticate_user(self, phone, password):
        cursor = self.conn.cursor()
        query = """
        SELECT id, name, phone, user_level_id, shop_id
        FROM users 
        WHERE phone = ? AND password = ? 
        """
        cursor.execute(query, (phone, self.hash_password(password)))
        data = cursor.fetchone()
        self.conn.close()
        if data:
            return User(data[0], data[1], data[2], data[3], data[4])
        else:
            return None 
    
    def save_user(self, name, phone, user_level_id, shop_id, password):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users(name, phone, user_level_id, shop_id, password, created_at, created_by) VALUES(?, ?, ?, ?, ?, NOW(), 0)", (name, phone, user_level_id, shop_id, self.hash_password(password)))
        self.conn.commit()
        user_id = cursor.lastrowid
        self.conn.close() 
        return user_id   
    
    def save_payment(self, bill_id, amount, payment_mode_id):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO payments(bill_id, amount, payment_mode_id, created_at, created_by) VALUES(?, ?, ?, NOW(), 0)", (bill_id, amount, payment_mode_id))
        self.conn.commit()
        payment_id = cursor.lastrowid
        self.conn.close() 
        return payment_id 
    
    def save_license(self, package, payment_id):
        key = uuid.uuid4()
        cursor = self.conn.cursor()
        query = """
        INSERT INTO licenses(key, package_id, payment_id, expires_at, created_at, created_by) 
        VALUES(?, ?, ?, NOW() + INTERVAL ?, NOW(), 0)
        """
        cursor.execute(query, (str(key), package.id, payment_id, f'+{package.validity} DAYS'))
        self.conn.commit()
        license_id = cursor.lastrowid
        self.conn.close()
        return license_id
    
    def save_company(self, name, license_id):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO companies(name, license_id, created_at, created_by) VALUES(?, ?, NOW(), 0)", (name, license_id))
        self.conn.commit()
        company_id = cursor.lastrowid
        self.conn.close() 
        return company_id 
    
    def save_shop(self, name, shop_type_id, company_id, location):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO shops(name, shop_type_id, company_id, location, created_at, created_by) VALUES(?, ?, ?, ?, NOW(), 0)", (name, shop_type_id, company_id, location))
        self.conn.commit()
        shop_id = cursor.lastrowid
        self.conn.close() 
        return shop_id
    
    def delete_website(website_id):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM websites WHERE id = ?', (website_id,))
        conn.commit()
        conn.close() 
      
    def get_license_id(self, id):
        cursor = self.conn.cursor()
        query = """
        SELECT id, key, package_id, expires_at
        FROM licenses 
        WHERE id = ? 
        """
        cursor.execute(query, (id,))
        data = cursor.fetchone()
        self.conn.close()
        if data:
            return Company(data[0], data[1], data[2], data[3])
        else:
            return None    
      
    def get_company_by_id(self, id):
        cursor = self.conn.cursor()
        query = """
        SELECT id, name, license_id
        FROM companies 
        WHERE id = ? 
        """
        cursor.execute(query, (id,))
        data = cursor.fetchone()
        self.conn.close()
        if data:
            return Company(data[0], data[1], data[2])
        else:
            return None    
      
    def get_shop_by_id(self, id):
        cursor = self.conn.cursor()
        query = """
        SELECT id, name, shop_type_id, company_id, location, phone_1, phone_2, paybill, account_no, till_no
        FROM shops 
        WHERE id = ? 
        """
        cursor.execute(query, (id,))
        data = cursor.fetchone()
        self.conn.close()
        if data:
            return Shop(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9])
        else:
            return None    
        
    def get_package_by_id(self, id):
        cursor = self.conn.cursor()
        query = """
        SELECT id, name, amount, description, color, validity
        FROM packages 
        WHERE id = ? 
        """
        cursor.execute(query, (id,))
        data = cursor.fetchone()
        self.conn.close()
        if data:
            return Package(data[0], data[1], data[2], data[3], data[4], data[5])
        else:
            return None    