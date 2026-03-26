CREATE DATABASE AuthDB;

USE AuthDB;

CREATE TABLE Users (
    id INT PRIMARY KEY IDENTITY,
    username VARCHAR(50),
    password VARCHAR(255),
    role VARCHAR(10) -- owner / seller
);

CREATE DATABASE ProductDB;

USE ProductDB;

CREATE TABLE Products (
    id INT PRIMARY KEY IDENTITY,
    name VARCHAR(100),
    buying_price FLOAT,
    selling_price FLOAT,
    quantity INT,
    qty_alert INT
);

CREATE DATABASE BillingDB;

USE BillingDB;

CREATE TABLE BillItems (
    id INT PRIMARY KEY IDENTITY,
    bill_id INT,
    product_id INT,
    quantity INT,
    price FLOAT
);

CREATE DATABASE ReturnDB;

USE ReturnDB

CREATE TABLE Returns (
    id INT PRIMARY KEY IDENTITY,
    product_id INT,
    quantity INT,
    refund_amount FLOAT,
    created_at DATETIME DEFAULT GETDATE()
);

select * from Products