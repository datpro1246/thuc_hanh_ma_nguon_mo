import sqlite3

# 1. Kết nối tới cơ sở dữ liệu
conn = sqlite3.connect("inventory.db")

# Tạo đối toượng 'cursor' để thực thi các câu lệnh SQL
cursor = conn.cursor()

# 2. Thao tác với Database và Table

# Lệnh SQL  tạo bảng products
sql1 = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price NUMERIC NOT NULL,
    quantity INTEGER    
)
"""

# Thực thi câu lệnh tạo bảng 
cursor.execute(sql1)
conn.commit() # lƯU THAY ĐỔI VÀO DB

# 3. CRUD
# 3.1 Thêm (INSERT)
products_data = [
    ("Laptop A100",999.99,15),
    ("Mouse Wỉeless X", 25.50,50),
    ("Monitor 27-inch", 249.00,10)
]

# Lệnh SQL để chèn dữ liệu. Dùng '? để tránh lỗi SQL Injection
sql2 = """
INSERT INTO products (name, price, quantity)
VALUES
(?,?,?)
"""

# Thêm nhiều bản ghi cùng lúc
cursor.executemany(sql2, products_data)
conn.commit() # Lưu thay đổi 

#3.2 read (select)
sql3 = "SELECT * FROM products"

#Thục thi truy vấn
cursor.execute(sql3)

# Lấy tất cả kết quả
all_products = cursor.fetchall()

# In tiêu đề 
print(f"{'ID':<4} | {'Tên Sản Phẩm':<20} | {'Giá':<10} | {'Số Lượng':<10}")
# Lặp và in ra
for p in all_products:
    print(f"{p[0]:<4} | {p[1]:<20} | {p[2]:<10} | {p[3]:<10}")
    
# 3.3 UPDATE
sql_update = """
UPDATE products
SET price = ?, quantity = ?
WHERE id = ?
"""

cursor.execute(sql_update, (899.99, 20, 1))
conn.commit()

print("Đã cập nhật sản phẩm có ID = 1")

# 3.4 DELETE
sql_delete = "DELETE FROM products WHERE id = ?"

cursor.execute(sql_delete, (2,))
conn.commit()

print("Đã xoá sản phẩm có ID = 2")
