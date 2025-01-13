import yaml

class Config:
  def __init__(self, file):
    self.file = file
    self.profile = {}  # Example, this should be populated from file
    self.load_config()
    self.companies_file = self.read_companies()

  def read_companies(self):
    companies_file = open(self.file, 'r')
    company_subdomains = []
    for company_subdomain in companies_file:
      company_subdomains.append(company_subdomain.strip())
    companies_file.close()
    return company_subdomains

  def write_company(self, company_subdomain):
    company_subdomains = self.read_companies()
    if company_subdomain in company_subdomains:
      return
    companies_file = open(self.file, 'a+')
    companies_file.writelines("\n"+company_subdomain)
    companies_file.close()

  def load_config(self):
      with open(self.file, 'r') as f:
          data = yaml.safe_load(f)
          if data:
              self.profile = data
