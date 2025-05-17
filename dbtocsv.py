import pandas as pd
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    f'SERVER={os.getenv("SQL_SERVER_HOST")};'
    f'DATABASE=ProductDB;'
    f'UID={os.getenv("SQL_SERVER_USER")};'
    f'PWD={os.getenv("SQL_SERVER_PASSWORD")}'
)
cursor = conn.cursor()

def fetch_data():
    query = """
    SELECT 
    p.id AS product_id,
    p.name AS product_name,
    p.created_at AS product_created_at,
    p.updated_at AS product_updated_at,
    t.id AS trademark_id,
    t.name AS trademark_name,
    
    pv.id AS product_variant_id,
    pv.name AS product_variant_name,
    MAX(CAST(pv.description AS VARCHAR(MAX))) AS product_variant_description,
    pv.status AS product_variant_status,
    pv.featured AS product_variant_featured,
    pv.created_at AS product_variant_created_at,
    pv.updated_at AS product_variant_updated_at,
    uc.id AS usage_category_id,
    uc.name AS usage_category_name,
    uc.status AS usage_category_status,
    
    pvd.id AS product_variant_detail_id,
    pv.name + ' - ' + c.name + ' - ' + m.name AS product_variant_detail_name,
    pvd.price,
    pvd.quantity,
    pvd.sale,
    pvd.status AS product_variant_detail_status,
    pvd.views_count,
    c.id AS color_id,
    c.name AS color_name,
    m.id AS memory_id,
    m.name AS memory_name,
    
    pi.id AS product_image_id,
    pi.path AS product_image_path,
    pi.avatar AS product_image_avatar,
    
    pf.id AS product_feedback_id,
    pf.customer_id,
    pf.feedback_rating,
    MAX(CAST(pf.feedback_text AS VARCHAR(MAX))) AS feedback_text,
    pf.created_at AS feedback_created_at,
    
    ipf.id AS img_product_feedback_id,
    ipf.image_path AS img_product_feedback_path,
    MAX(CAST(ipf.description AS VARCHAR(MAX))) AS img_product_feedback_description,

    STRING_AGG(a.name + ': ' + av.value, '; ') AS attributes

FROM products p
LEFT JOIN trademarks t ON p.trademark_id = t.id
LEFT JOIN products_variants pv ON pv.product_id = p.id
LEFT JOIN usage_categories uc ON pv.usage_category_id = uc.id
LEFT JOIN product_variant_details pvd ON pvd.product_variant_id = pv.id
LEFT JOIN colors c ON pvd.color_id = c.id
LEFT JOIN memories m ON pvd.memory_id = m.id
LEFT JOIN products_images pi ON pi.product_variant_detail_id = pvd.id
LEFT JOIN product_feedbacks pf ON pf.product_variant_id = pv.id
LEFT JOIN img_product_feedback ipf ON ipf.product_feedback_id = pf.id
LEFT JOIN attribute_values av ON av.product_variant_id = pv.id
LEFT JOIN attributes a ON av.attribute_id = a.id

GROUP BY 
    p.id, p.name, p.created_at, p.updated_at,
    t.id, t.name,
    pv.id, pv.name, pv.status, pv.featured, pv.created_at, pv.updated_at,
    uc.id, uc.name, uc.status,
    pvd.id, pvd.price, pvd.quantity, pvd.sale, pvd.status, pvd.views_count,
    c.id, c.name,
    m.id, m.name,
    pi.id, pi.path, pi.avatar,
    pf.id, pf.customer_id, pf.feedback_rating, pf.created_at,
    ipf.id, ipf.image_path,
    pv.name + ' - ' + c.name + ' - ' + m.name

    """
    df = pd.read_sql(query, conn)
    return df

df = fetch_data()
df.to_csv("product_data.csv", index=False, encoding="utf-8-sig")

print("✅ Dữ liệu đã được xuất ra file product_data.csv")
