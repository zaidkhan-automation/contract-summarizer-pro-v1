from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

os.makedirs("data", exist_ok=True)
path = os.path.join("data", "sample_contract.pdf")

c = canvas.Canvas(path, pagesize=A4)
width, height = A4

c.setFont("Helvetica-Bold", 16)
c.drawString(50, height - 80, "MASTER SERVICES AGREEMENT")

c.setFont("Helvetica", 11)
c.drawString(50, height - 120, "This Master Services Agreement (\"Agreement\") is made on 01 January 2025 between:")
c.drawString(50, height - 140, "Provider: Alpha Tech Solutions Pvt Ltd")
c.drawString(50, height - 160, "Client: Zaid Broski")
c.drawString(50, height - 190, "1. SERVICES")
c.drawString(70, height - 210, "Provider agrees to provide software development and automation services as described in SOW.")
c.drawString(50, height - 240, "2. TERM")
c.drawString(70, height - 260, "The term of this Agreement shall commence on the Effective Date and continue for 12 months.")
c.drawString(50, height - 290, "3. FEES & PAYMENT")
c.drawString(70, height - 310, "Client will pay Provider INR 1,50,000 per milestone within 30 days of invoice.")
c.drawString(50, height - 340, "4. CONFIDENTIALITY")
c.drawString(70, height - 360, "Each party shall keep confidential information secure and not disclose to third parties.")
c.drawString(50, height - 390, "5. TERMINATION")
c.drawString(70, height - 410, "Either party may terminate on 30 days written notice for material breach.")
c.drawString(50, height - 450, "Signatures:")
c.drawString(50, height - 480, "Provider: ____________________    Date: _//_")
c.drawString(50, height - 500, "Client:   ____________________    Date: _//_")

c.showPage()
c.save()

print("✅ Created data/sample_contract.pdf")