CREATE DATABASE kaplan_db;
GO
USE kaplan_db;
GO
CREATE TABLE fp_enrollment (
    id             INT IDENTITY(1,1) PRIMARY KEY,
    period         VARCHAR(20),
    program        VARCHAR(100),
    business_unit  VARCHAR(50),
    enrolled_count INT,
    drop_rate      DECIMAL(5,2),
    created_at     DATETIME DEFAULT GETDATE()
);
GO
INSERT INTO fp_enrollment VALUES ('Q1_2025','MBA Program','Higher Education',1250,8.5,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q1_2025','Data Science','Higher Education',980,6.2,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q1_2025','Bar Exam Prep','Supplemental',2100,12.1,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q1_2025','CFA Prep','Supplemental',1450,9.8,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q2_2025','MBA Program','Higher Education',1380,7.9,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q2_2025','Data Science','Higher Education',1050,5.8,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q2_2025','Bar Exam Prep','Supplemental',2250,11.5,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q2_2025','CFA Prep','Supplemental',1580,9.2,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q3_2025','MBA Program','Higher Education',1480,7.2,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q3_2025','Data Science','Higher Education',1120,5.4,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q3_2025','Bar Exam Prep','Supplemental',2380,10.8,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q3_2025','CFA Prep','Supplemental',1680,8.7,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q1_2024','MBA Program','Higher Education',1100,9.8,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q1_2024','Data Science','Higher Education',850,7.5,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q1_2024','Bar Exam Prep','Supplemental',1900,13.2,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q1_2024','CFA Prep','Supplemental',1280,11.1,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q2_2024','MBA Program','Higher Education',1200,9.1,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q2_2024','Bar Exam Prep','Supplemental',2050,12.4,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q3_2024','MBA Program','Higher Education',1320,8.4,DEFAULT);
INSERT INTO fp_enrollment VALUES ('Q3_2024','Bar Exam Prep','Supplemental',2180,11.8,DEFAULT);
GO
