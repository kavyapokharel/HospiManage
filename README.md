# Hospital Management System (C++)

This is a console-based Hospital Management System written in C++.
The program allows users to manage patient records using binary file storage. It supports adding, viewing, searching, modifying, deleting, and transposing patient data.

All records are stored in a binary file (hospital.dat) for persistence.

# Features

- Adds new patient records
- Displays all patient records
- Searches patient by ID
- Modifies existing patient records
- Deletes specific patient records
- Transposes records within an ID range
- Displays transposed records
- Erases all records

# Data Stored

Each patient record contains:

- Patient ID
- Patient Name
- Age
- Gender
- Marital Status
- Father’s Name (if applicable)
- Mother’s Name (if applicable)
- Husband’s Name (if applicable)
- Referrer’s Name & Relation
- Mobile Number

# File Structure

hospital.dat → Main binary file storing patient records
hos.dat → Temporary file used for delete/transpose operations

# Technologies Used

- C++
- File Handling 
- Binary File Storage
- String Handling 
- Console I/O 
- Windows-specific functions 

