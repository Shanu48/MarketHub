CREATE DATABASE MarketHub;
USE MarketHub;

CREATE TABLE User (
    userID VARCHAR(10) PRIMARY KEY,
    password VARCHAR(20) NOT NULL
);


CREATE TABLE Supplier (
    userID VARCHAR(10),
    sName VARCHAR(20) NOT NULL,
    email VARCHAR(50) NOT NULL,
    phoneNo INT NOT NULL,
    FOREIGN KEY (userID) REFERENCES User(userID)
);


CREATE TABLE Customer (
    userID VARCHAR(10),
    cName VARCHAR(20) NOT NULL,
    email VARCHAR(50) NOT NULL,
    phoneNo INT NOT NULL,
    FOREIGN KEY (userID) REFERENCES User(userID)
);


CREATE TABLE Address (
    userID VARCHAR(10),
    houseNo VARCHAR(10) NOT NULL,
    streetName VARCHAR(50) NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    pin INT NOT NULL,
    FOREIGN KEY (userID) REFERENCES User(userID)
);


CREATE TABLE Category (
    categoryName VARCHAR(30) PRIMARY KEY,
    description VARCHAR(50) NOT NULL
);

CREATE TABLE Product (
    productID VARCHAR(10) PRIMARY KEY,
    pName VARCHAR(50) NOT NULL,
    description VARCHAR(100) NOT NULL,
    price INT NOT NULL,
    unit VARCHAR(10) NOT NULL,
    categoryName VARCHAR(50),
    userID VARCHAR(10),
    FOREIGN KEY (categoryName) REFERENCES Category(categoryName),
    FOREIGN KEY (userID) REFERENCES Supplier(userID)
);

-- expiry date has been added too to the products table

CREATE TABLE Orders (
    orderID VARCHAR(10) PRIMARY KEY,
    date DATE NOT NULL,
    quantity INT NOT NULL,
    totalPrice INT NOT NULL,
    userID VARCHAR(10),
    FOREIGN KEY (userID) REFERENCES Customer(userID)
);


CREATE TABLE Returns (
    returnID VARCHAR(10) PRIMARY KEY,
    reason VARCHAR(100) NOT NULL,
    status VARCHAR(10) NOT NULL,
    orderID VARCHAR(10),
    FOREIGN KEY (orderID) REFERENCES Orders(orderID)
);


CREATE TABLE Transport (
    transportID VARCHAR(10) PRIMARY KEY,
    vehicleNo VARCHAR(10) NOT NULL,
    driverName VARCHAR(20) NOT NULL,
    status VARCHAR(10) NOT NULL,
    orderID VARCHAR(10),
    FOREIGN KEY (orderID) REFERENCES Orders(orderID)
);


CREATE TABLE Warehouse (
    warehouseID VARCHAR(10) PRIMARY KEY,
    location VARCHAR(50) NOT NULL,
    capacity INT NOT NULL
);


CREATE TABLE Supplies (
    userID VARCHAR(10),
    warehouseID VARCHAR(10),
    PRIMARY KEY (userID, warehouseID),
    FOREIGN KEY (userID) REFERENCES Supplier(userID),
    FOREIGN KEY (warehouseID) REFERENCES Warehouse(warehouseID)
);


CREATE TABLE Contains (
    orderID VARCHAR(10),
    productID VARCHAR(10),
    productQuantity INT NOT NULL,
    PRIMARY KEY (orderID, productID),
    FOREIGN KEY (orderID) REFERENCES Orders(orderID),
    FOREIGN KEY (productID) REFERENCES Product(productID)
);


CREATE TABLE Storage (
    warehouseID VARCHAR(10),
    productID VARCHAR(10),
    productQuantity INT NOT NULL,
    PRIMARY KEY (warehouseID, productID),
    FOREIGN KEY (warehouseID) REFERENCES Warehouse(warehouseID),
    FOREIGN KEY (productID) REFERENCES Product(productID)
);

CREATE TABLE Discount (
    discountID VARCHAR(10) PRIMARY KEY,
    discountPercentage INT NOT NULL,
    startDate DATE NOT NULL,
    endDate DATE NOT NULL,
    productID VARCHAR(10),
    FOREIGN KEY (productID) REFERENCES Product(productID)
);

CREATE TABLE Fulfill (
    warehouseID VARCHAR(10),
    orderID VARCHAR(10),
    productID VARCHAR(10),
    PRIMARY KEY (warehouseID, orderID, productID),
    FOREIGN KEY (warehouseID) REFERENCES Warehouse(warehouseID),
    FOREIGN KEY (orderID) REFERENCES Orders(orderID),
    FOREIGN KEY (productID) REFERENCES Contains(productID)
);

CREATE TABLE Cart (
    userID VARCHAR(10),
    productID VARCHAR(10),
    quantity INT,
    PRIMARY KEY (userID, productID),
    FOREIGN KEY (productID) REFERENCES product(productID),
    FOREIGN KEY (userID) REFERENCES customer(userID)
);

CREATE TABLE Shipment (
    shipmentID VARCHAR(10) PRIMARY KEY,
    transportID VARCHAR(10),
    orderID VARCHAR(10),
    status ENUM('Pending', 'In Transit', 'Delivered') NOT NULL,
    startTime DATETIME NOT NULL,
    estimatedDelivery DATETIME NOT NULL,
    FOREIGN KEY (transportID) REFERENCES Transport(transportID),
    FOREIGN KEY (orderID) REFERENCES Orders(orderID)
);

-- Sample Data for User Table
INSERT INTO User (userID, password) VALUES
('S001', 'pass@123'),
('S002', 'pass@123'),
('S003', 'pass@123'),
('S004', 'pass@123'),
('S005', 'pass@123'),
('C001', 'cust@123'),
('C002', 'cust@123'),
('C003', 'cust@123'),
('C004', 'cust@123'),
('C005', 'cust@123');

-- Sample Data for Customer Table
INSERT INTO Customer (userID, cName, email, phoneNo) VALUES
('C001', 'Customer One', 'customer1@example.com', 9998887771),
('C002', 'Customer Two', 'customer2@example.com', 9998887772),
('C003', 'Customer Three', 'customer3@example.com', 9998887773),
('C004', 'Customer Four', 'customer4@example.com', 9998887774),
('C005', 'Customer Five', 'customer5@example.com', 9998887775);

-- Sample Data for Supplier Table
INSERT INTO Supplier (userID, sName, email, phoneNo) VALUES 
('S001', 'Supplier One', 'supplier1@example.com', '9876543210'),
('S002', 'Supplier Two', 'supplier2@example.com', '9876543211'),
('S003', 'Supplier Three', 'supplier3@example.com', '9876543212'),
('S004', 'Supplier Four', 'supplier4@example.com', '9876543213'),
('S005', 'Supplier Five', 'supplier5@example.com', '9876543214');

