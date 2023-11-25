from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import boto3
from datetime import datetime

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(String(255), index=True)
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

# Configuração do cliente do CloudWatch
cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')

def send_custom_metric(metric_name, value):
    cloudwatch.put_metric_data(
        MetricData=[
            {
                'MetricName': metric_name,
                'Dimensions': [
                    {
                        'Name': 'Application',
                        'Value': 'MyFastAPIApp'
                    },
                ],
                'Unit': 'Count',
                'Value': value
            },
        ],
        Namespace='MyAppMetrics'
    )

@app.post("/items/")
def create_item(name: str, description: str):
    db = SessionLocal()
    new_item = Item(name=name, description=description)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    send_custom_metric('ItemsCreated', 1)
    return new_item

@app.get("/items/")
def read_items():
    db = SessionLocal()
    items = db.query(Item).all()
    send_custom_metric('ItemsRead', len(items))
    return items

@app.get("/items/{item_id}")
def read_item(item_id: int):
    db = SessionLocal()
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    send_custom_metric('ItemsRead', 1)
    return item

@app.put("/items/{item_id}")
def update_item(item_id: int, name: str, description: str):
    db = SessionLocal()
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    item.name = name
    item.description = description
    db.commit()
    send_custom_metric('ItemsUpdated', 1)
    return item

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    db = SessionLocal()
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    send_custom_metric('ItemsDeleted', 1)
    return {"detail": "Item deleted successfully"}

