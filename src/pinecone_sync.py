import os
import pyodbc
import pandas as pd
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from tqdm.auto import tqdm
import time
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Pinecone configuration
api_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=api_key)

spec = ServerlessSpec(cloud="aws", region="us-east-1")

index_name = 'product-catalog-1'
existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=768,
        metric='dotproduct',
        spec=spec
    )
    while not pc.describe_index(index_name).status['ready']:
        time.sleep(1)

index = pc.Index(index_name)
time.sleep(1)

# SQL Server configuration
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    f'SERVER={os.getenv("SQL_SERVER_HOST")};'
    f'DATABASE=ProductDB;'
    f'UID={os.getenv("SQL_SERVER_USER")};'
    f'PWD={os.getenv("SQL_SERVER_PASSWORD")}'
)
cursor = conn.cursor()

# Google Gemini Embedding Model
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
embed_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

def fetch_data():
    query = """
    SELECT 
        p.name AS product_name,
        pv.name AS variant_name,
        pv.name + ' - ' + c.name + ' - ' + m.name AS pvd_name,
        pvd.price,
        pvd.status,
        c.name AS color_name,
        m.name AS memory_name,
        STRING_AGG(a.name + ': ' + av.value, ', ') AS attributes
    FROM products p
    JOIN products_variants pv ON p.id = pv.product_id
    JOIN product_variant_details pvd ON pv.id = pvd.product_variant_id
    JOIN attribute_values av ON av.product_variant_id = pv.id
    JOIN attributes a ON av.attribute_id = a.id
    JOIN colors c ON c.id = pvd.color_id
    JOIN memories m ON pvd.memory_id = m.id
    GROUP BY p.name, pv.name, pv.name + ' - ' + c.name + ' - ' + m.name, 
             pvd.price, pvd.status, c.name, m.name
    """
    df = pd.read_sql(query, conn)
    return df

def sync_with_pinecone(data):
    batch_size = 100
    total_batches = (len(data) + batch_size - 1) // batch_size

    for i in tqdm(range(0, len(data), batch_size), desc='Processing Batches', unit='batch', total=total_batches):
        i_end = min(len(data), i + batch_size)
        batch = data.iloc[i:i_end]

        ids = [f"{row['pvd_name']}_{i}" for i, row in batch.iterrows()]

        texts = [
            f"{row['pvd_name']}. Giá: {row['price']}. Màu sắc: {row['color_name']}. Bộ nhớ: {row['memory_name']}. "
            f"Trạng thái: {row['status']}. Thuộc tính: {row['attributes']}"
            for _, row in batch.iterrows()
        ]

        embeds = embed_model.embed_documents(texts)

        metadata = [
        {
            'ProductName': row['product_name'],
            'VariantName': row['variant_name'],
            'Color': row['color_name'],
            'Memory': row['memory_name'],
            'Price': row['price'],
            'Status': row['status'],
            'Attributes': row['attributes'],
            'text': texts[i]  
        }
            for i, row in batch.iterrows()
        ]

        print(metadata)


        with tqdm(total=len(ids), desc='Upserting Vectors', unit='vector') as upsert_pbar:
            index.upsert(vectors=zip(ids, embeds, metadata))
            upsert_pbar.update(len(ids))

def main():
    data = fetch_data()
    sync_with_pinecone(data)

if __name__ == "__main__":
    main()

cursor.close()
conn.close()
