import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configura el navegador Chrome y la extensión para resolver captchas
options = webdriver.ChromeOptions()
options.add_extension('2captcha_crx.crx')driver = webdriver.Chrome(options=options)

# Función para resolver captchas con 2captcha
def resolve_captcha(driver):    # Encontrar el elemento del captcha y hacer clic en él
    captcha_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#captcha > div > iframe')))
driver.switch_to.frame(captcha_element)
captcha_image = driver.find_element_by_tag_name('img')
captcha_url = captcha_image.get_attribute('src')# Enviar la imagen del captcha a 2captcha para resolución
response = requests.post('https://2captcha.com/in.php', files={'file': open(captcha_url, 'rb')})
captcha_id = response.text.split('|')[1]
# Esperar la respuesta de 2captcha
while True:
    response = requests.get(f'https://2captcha.com/res.php?key=YOUR_API_KEY&action=get&id={captcha_id}')        
if 'OK' in response.text:
        break

# Obtener el resultado del captcha
captcha_captcha = response.text.split('|')[1]
driver.find_element_by_id('captcha_answer').send_keys(captcha)
driver.find_element_by_id('submit_button').click()
Iniciar sesión en TikTok

driver.get('https://www.tiktok.com/')
driver.find_element_by_link_text('Iniciar sesión').click()
driver.find_element_by_name('username').send_keys('tu_usuario')
driver.find_element_by_name('password').send_keys('tu_contraseña')
driver.find_element_by_xpath('//button[@type="submit"]').click()
Navegar a la página de la cuenta objetivo

target_account = 'usuario_objetivo'
driver.get(f'https://www.tiktok.com/@{target_account}')# Encontrar el botón de denunciar y hacer clic en él
denunciar_button = WebDriverWait(driver, 10)
until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Denunciar"]')))
denunciar_button.click()

try:
resolve_captcha(driver)except:
pass
motivo_denuncia = 'Contenido inapropiado'
driver.find_element_by_xpath(f'//span[contains(text(),"{motivo_denuncia}")]/parent::label').click()

Ingresar detalles adicionales (opcional)

detalles_denuncia = 'Este usuario publica contenido pornográfico y violento.'
driver.find_element_by_name('report_reason_details').send_keys(detalles_denuncia)# Confirmar la denuncia
confirmar_button = driver.find_element_by_xpath('//button[contains(text(),"Confirmar")]')
confirmar_button.click()

print(f'Denuncia enviada con éxito a la cuenta {target_account}')

driver.quit()

print('Script finalizado.')
