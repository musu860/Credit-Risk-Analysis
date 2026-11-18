-- Q1 | Basic | Retrieve all records from the loan_data table
SELECT * FROM loan_data LIMIT 1000;

-- Q2 | Basic | Loan applications with contract type and contract status
SELECT SK_ID_CURR, NAME_CONTRACT_TYPE, NAME_CONTRACT_STATUS FROM loan_data;

-- Q3 | Basic | Applications where contract status is 'Approved'
SELECT * FROM loan_data WHERE NAME_CONTRACT_STATUS = 'Approved' LIMIT 1000;

-- Q4 | Basic | Applications where contract status is 'Refused'
SELECT * FROM loan_data WHERE NAME_CONTRACT_STATUS = 'Refused' LIMIT 1000;

-- Q5 | Basic | Applications belonging to the 'Repeater' client type
SELECT * FROM loan_data WHERE NAME_CLIENT_TYPE = 'Repeater' LIMIT 1000;

-- Q6 | Aggregation | Total number of loan applications
SELECT COUNT(*) AS total_applications FROM loan_data;

-- Q7 | Aggregation | Total credit amount across all applications
SELECT ROUND(SUM(AMT_CREDIT), 2) AS total_credit_amount FROM loan_data;

-- Q8 | Aggregation | Average loan application amount
SELECT ROUND(AVG(AMT_APPLICATION), 2) AS avg_application_amount FROM loan_data;

-- Q9 | Aggregation | Number of applications for each contract status
SELECT NAME_CONTRACT_STATUS, COUNT(*) AS applications
FROM loan_data GROUP BY NAME_CONTRACT_STATUS ORDER BY applications DESC;

-- Q10 | Aggregation | Average annuity amount for each contract type
SELECT NAME_CONTRACT_TYPE, ROUND(AVG(AMT_ANNUITY), 2) AS avg_annuity
FROM loan_data GROUP BY NAME_CONTRACT_TYPE ORDER BY avg_annuity DESC;

-- Q11 | Filter | Applications where credit amount is greater than 500,000
SELECT SK_ID_CURR, NAME_CONTRACT_TYPE, NAME_CONTRACT_STATUS, AMT_CREDIT
FROM loan_data WHERE AMT_CREDIT > 500000 ORDER BY AMT_CREDIT DESC LIMIT 1000;

-- Q12 | Filter | Applications where down payment is greater than 50,000
SELECT SK_ID_CURR, NAME_CONTRACT_TYPE, AMT_CREDIT, AMT_DOWN_PAYMENT
FROM loan_data WHERE AMT_DOWN_PAYMENT > 50000 ORDER BY AMT_DOWN_PAYMENT DESC;

-- Q13 | Filter | Number of applications for each client type
SELECT NAME_CLIENT_TYPE, COUNT(*) AS applications
FROM loan_data GROUP BY NAME_CLIENT_TYPE ORDER BY applications DESC;

-- Q14 | Filter | Average credit amount for each loan contract status
SELECT NAME_CONTRACT_STATUS, ROUND(AVG(AMT_CREDIT), 2) AS avg_credit
FROM loan_data GROUP BY NAME_CONTRACT_STATUS ORDER BY avg_credit DESC;

-- Q15 | Filter | Top 5 product combinations by number of applications
SELECT PRODUCT_COMBINATION, COUNT(*) AS applications
FROM loan_data GROUP BY PRODUCT_COMBINATION ORDER BY applications DESC LIMIT 5;

-- Q16 | Financial | Total credit amount for approved and refused applications separately
SELECT NAME_CONTRACT_STATUS, ROUND(SUM(AMT_CREDIT), 2) AS total_credit
FROM loan_data WHERE NAME_CONTRACT_STATUS IN ('Approved', 'Refused')
GROUP BY NAME_CONTRACT_STATUS;

-- Q17 | Financial | Top 3 contract types with highest average credit amount
SELECT NAME_CONTRACT_TYPE, ROUND(AVG(AMT_CREDIT), 2) AS avg_credit
FROM loan_data GROUP BY NAME_CONTRACT_TYPE ORDER BY avg_credit DESC LIMIT 3;

-- Q18 | Financial | Total application amount for each payment type
SELECT NAME_PAYMENT_TYPE, ROUND(SUM(AMT_APPLICATION), 2) AS total_application_amount
FROM loan_data GROUP BY NAME_PAYMENT_TYPE ORDER BY total_application_amount DESC;

-- Q19 | Financial | Top 5 seller industries by total credit amount
SELECT NAME_SELLER_INDUSTRY, ROUND(SUM(AMT_CREDIT), 2) AS total_credit
FROM loan_data GROUP BY NAME_SELLER_INDUSTRY ORDER BY total_credit DESC LIMIT 5;

-- Q20 | Financial | Approval percentage for each contract type
SELECT NAME_CONTRACT_TYPE,
       COUNT(*) AS total_applications,
       SUM(CASE WHEN NAME_CONTRACT_STATUS = 'Approved' THEN 1 ELSE 0 END) AS approved,
       ROUND(100.0 * SUM(CASE WHEN NAME_CONTRACT_STATUS = 'Approved' THEN 1 ELSE 0 END) / COUNT(*), 2) AS approval_pct
FROM loan_data GROUP BY NAME_CONTRACT_TYPE ORDER BY approval_pct DESC;
