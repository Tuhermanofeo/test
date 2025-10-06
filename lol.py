python
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By

options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Ejecutar el navegador en segundo plano
driver = webdriver.Chrome(options=options)
def get_saved_passwords():
driver.get('chrome://settings/credentials') # Página de contraseñas guardadas en Chrome
passwords = driver.find_elements_by_css_selector('div.credential-item') # Encontrar todos los elementos de contraseña
saved_passwords = [] 
for password in passwords:
    origin = password.find_element_by_css_selector('span.origin').text  # Obtener la página/origen
    username = password.find_element_by_css_selector('span.username').
