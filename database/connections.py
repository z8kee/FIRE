import psycopg2, dotenv, os
from psycopg2.extras import RealDictCursor

dotenv.load_dotenv()

class SECRepository:
    def __init__(self, dbname, user, password, host='localhost', port=5432):
        self.connection = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                company_id SERIAL PRIMARY KEY,
                ticker VARCHAR(10) UNIQUE NOT NULL,
                name TEXT NOT NULL,
                cik VARCHAR(20) UNIQUE NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                document_id SERIAL PRIMARY KEY,
                company_id INTEGER REFERENCES companies(company_id),
                accession_number TEXT UNIQUE NOT NULL,
                filing_type VARCHAR(10) NOT NULL,
                filing_date DATE NOT NULL,
                acceptance_datetime TIMESTAMPTZ,
                source_url TEXT
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id SERIAL PRIMARY KEY,
                document_id INTEGER REFERENCES documents(document_id),
                section TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                UNIQUE(document_id, section, chunk_index)
            )
        ''')
    def commit(self):
        self.connection.commit()

    def insert_company(self, ticker, name, cik):
        self.cursor.execute('''
            INSERT INTO companies (ticker, name, cik)
            VALUES (%s, %s, %s)
            ON CONFLICT (ticker) DO NOTHING
            RETURNING company_id
        ''', (ticker, name, cik))
        company_id = self.cursor.fetchone()
        if company_id is None:
            self.cursor.execute('SELECT company_id FROM companies WHERE ticker = %s', (ticker,))
            company_id = self.cursor.fetchone()[0]
        else:
            company_id = company_id[0]
        self.commit()
        return company_id

    def insert_document(self, company_id, accession_number, filing_type, filing_date, acceptance_datetime, source_url):
        self.cursor.execute('''
            INSERT INTO documents (company_id, accession_number, filing_type, filing_date, acceptance_datetime, source_url)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (accession_number) 
            DO UPDATE SET
                acceptance_datetime = EXCLUDED.acceptance_datetime

            RETURNING document_id
        ''', (company_id, accession_number, filing_type, filing_date, acceptance_datetime, source_url))
        document_id = self.cursor.fetchone()
        if document_id is None:
            self.cursor.execute('SELECT document_id FROM documents WHERE accession_number = %s', (accession_number,))
            document_id = self.cursor.fetchone()[0]
        else:
            document_id = document_id[0]
        self.commit()
        return document_id

    def insert_chunk(self, document_id, section, chunk_index, text):
        self.cursor.execute('''
            INSERT INTO chunks (document_id, section, chunk_index, text)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (document_id, section, chunk_index)
            DO NOTHING
            ''', (document_id, section, chunk_index, text)
            )
        self.commit()

    def get_chunks(self):
        self.cursor.execute("""
        SELECT
            ch.chunk_id,
            ch.document_id,
            ch.text,
            ch.section,
            d.filing_type,
            d.filing_date,
            c.ticker
        FROM chunks ch

        JOIN documents d
            ON ch.document_id = d.document_id
        JOIN companies c
            ON d.company_id = c.company_id
        
        ORDER BY ch.chunk_id
        """)

        return self.cursor.fetchall()

    def get_specific_chunk(self, chunk_id):
        self.cursor.execute("""
            SELECT
                ch.text,
                ch.section,
                d.filing_type,
                d.filing_date,
                c.ticker
            FROM chunks ch
            JOIN documents d
                ON ch.document_id = d.document_id
            JOIN companies c
                ON d.company_id = c.company_id
            WHERE ch.chunk_id = %s
        """, (chunk_id,))

        return self.cursor.fetchone()

    def get_docs_missing_timestamp(self):
        self.cursor.execute("""
            SELECT
                d.document_id,
                d.accession_number,
                c.ticker
            FROM documents d
            JOIN companies c
                ON d.company_id = c.company_id
            WHERE d.acceptance_datetime IS NULL
        """)

        return self.cursor.fetchall()

    def update_acceptance_datetime(self, document_id, acceptance_datetime):
        self.cursor.execute("""
            UPDATE documents
            SET acceptance_datetime = %s
            WHERE document_id = %s
        """, (
            acceptance_datetime,
            document_id
        ))
    def get_document_timestamps(self):
        self.cursor.execute("""
            SELECT
                document_id,
                acceptance_datetime
            FROM documents
            WHERE acceptance_datetime IS NOT NULL
            ORDER BY document_id       
        """)

        return self.cursor.fetchall()
      
    def close(self):
        self.cursor.close()
        self.connection.close()

