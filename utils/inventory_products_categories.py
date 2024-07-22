from flask import render_template, request
from flask_login import current_user

class InventoryProductsCategories():
    def __init__(self, db): 
        self.db = db

    def __call__(self):
        shop = self.db.get_shop_by_id(current_user.shop_id) 
        company = self.db.get_company_by_id(shop.company_id)
        license = self.db.get_license_id(company.license_id)
        
        if request.method == 'POST':       
            if request.form['action'] == 'add':
                name = request.form['name']
                self.db.save_product_category(name)   
                   
            elif request.form['action'] == 'delete':
                id = request.form['item_id']
                self.db.delete_product_category(id) 
                
            elif request.form['action'] == 'update':
                id = request.form['id']
                name = request.form['name']    
                self.db.update_product_category(id, name)
                return 'success'
        
        product_categories = self.db.fetch_product_categories()
        return render_template('inventory/products-categories.html', shop=shop, company=company, license=license, product_categories=product_categories, page_title='Product Categories')
