CREATE DATABASE ShopDB;
USE ShopDB;

CREATE TABLE Users (
    id INT PRIMARY KEY IDENTITY,
    username VARCHAR(50),
    password VARCHAR(255),
    role VARCHAR(10) -- owner / seller
);

CREATE TABLE Products (
    id INT PRIMARY KEY IDENTITY,
    name VARCHAR(100),
    buying_price FLOAT,
    selling_price FLOAT,
    quantity INT,
    qty_alert INT
);

CREATE TABLE BillItems (
    id INT PRIMARY KEY IDENTITY,
    bill_id INT,
    product_id INT,
    quantity INT,
    price FLOAT
);

CREATE TABLE Returns (
    id INT PRIMARY KEY IDENTITY,
    product_id INT,
    quantity INT,
    refund_amount FLOAT,
    created_at DATETIME DEFAULT GETDATE()
);


