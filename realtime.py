import torch
from torchvision import transforms
from inferencer import Inferencer
from pasticheModel import PasticheModel
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import cv2
import json
from ultralytics import YOLO
import json
from PIL import Image
import cv2
import numpy as np
import matplotlib.pyplot as plt


model = YOLO('best.pt')
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

num_styles = 16
image_size = 256
model_save_dir = "style16/pastichemodel-FINAL.pth"

pastichemodel = PasticheModel(num_styles)

inference = Inferencer(pastichemodel,device,image_size)
inference.load_model_weights(model_save_dir)

captura = cv2.VideoCapture(0)

def portal_img(img):# Converter de BGR para RGB
    img_PIL = Image.fromarray(img)
    # print(img_PIL.mode)
    img_PIL.thumbnail((image_size,image_size),Image.ANTIALIAS)
    styled_img = inference.eval_image(img_PIL, 1,5,0.0)
    
    results = model(img, verbose=False)
    height, width, _ = img.shape
    styled_img = np.array(styled_img)
    styled_img = cv2.cvtColor(styled_img, cv2.COLOR_RGB2BGR)  # Converter de RGB para BGR

    res_json = json.loads(results[0].tojson())
    index = 0
    higher_conf = 0
    boxes = []
    label = 0
    for i, result in enumerate(res_json):
        if result['confidence'] > higher_conf:
            index = i
            higher_conf = result['confidence']
            boxes = result['box']
            label = result['class']
    if label != 0:
        mask_door = results[index].masks.data[index].cpu().numpy() * 255
        mask_door = cv2.cvtColor(mask_door.astype(np.uint8), cv2.COLOR_GRAY2BGR)
        mask_door = cv2.resize(mask_door, (width, height))

        x1 = int(boxes['x1'])
        y1 = int(boxes['y1'])
        x2 = int(boxes['x2'])
        y2 = int(boxes['y2'])
        #Colando o bounding box estilizado na foto original
        #Sem usar convexHull
        # aux = img.copy()
        # aux = cv2.cvtColor(aux, cv2.COLOR_RGB2BGR)
        # source_image = cv2.resize(styled_img, (width, height))
        # cropped_image = source_image[y1:y2, x1:x2]
        # aux[y1:y2, x1:x2] = cropped_image
        # image_s = aux
        # image_s = cv2.resize(image_s, (width, height))
        gray = cv2.cvtColor(mask_door, cv2.COLOR_BGR2GRAY)

        _, threshold = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        largest_contour = max(contours, key=cv2.contourArea)

        hull = cv2.convexHull(largest_contour)

        convex_hull_image = np.zeros(mask_door.shape[:2], dtype=np.uint8)

        cv2.drawContours(convex_hull_image, [hull], 0, 255, thickness=cv2.FILLED)

        convex_hull_image = cv2.resize(convex_hull_image, (img.shape[1], img.shape[0]))
        styled_img = cv2.resize(styled_img, (img.shape[1], img.shape[0]))

        moldura = cv2.bitwise_and(styled_img, styled_img, mask=convex_hull_image)
        moldura_mask_inv = cv2.bitwise_not(convex_hull_image) # Inverter a máscara
        moldura_mask_inv = cv2.resize(moldura_mask_inv, (img.shape[1], img.shape[0]))# Redimensionar a máscara para ter o mesmo tamanho da foto original
        moldura_mask_inv = moldura_mask_inv.astype(np.uint8)
        foto_original_bg = cv2.bitwise_and(img, img, mask=moldura_mask_inv)# Aplicar a máscara invertida na foto original para obter a área fora da moldura
        foto_estilizada_final = cv2.add(foto_original_bg, moldura)
        foto_estilizada_final = cv2.cvtColor(foto_estilizada_final, cv2.COLOR_BGR2RGB)


        #Colando a moldura da porta sem estilo
        image_original = cv2.resize(img, (width, height))
        moldura_porta = cv2.bitwise_and(image_original, mask_door)
        moldura_porta = cv2.cvtColor(moldura_porta, cv2.COLOR_RGB2BGR)

        # Redimensionar a moldura da porta para ter as mesmas dimensões da foto estilizada
        moldura_porta_redimensionada = cv2.resize(moldura_porta, (width, height))
        plt.imshow(moldura_porta_redimensionada)
        plt.show()

        # Criar a máscara inversa
        mascara_inversa = cv2.bitwise_not(mask_door)

        # Aplicar a máscara inversa à foto estilizada
        mascara_inversa = cv2.resize(mascara_inversa, (width, height))
        foto_estilizada_sem_moldura = cv2.bitwise_and(foto_estilizada_final, mascara_inversa)

        # Combinar a moldura redimensionada e a foto estilizada sem moldura
        foto_final = cv2.bitwise_or(moldura_porta_redimensionada, foto_estilizada_sem_moldura)
        return cv2.cvtColor(foto_final, cv2.COLOR_BGR2RGB)
    else:
        return img

cv2.namedWindow('Estilo em Tempo Real', cv2.WINDOW_NORMAL)

# Define o tamanho da janela
cv2.resizeWindow('Estilo em Tempo Real', 2400, 1800) 
fps = captura.get(cv2.CAP_PROP_FPS)
width = int(captura.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(captura.get(cv2.CAP_PROP_FRAME_HEIGHT))
# Definir as configurações do vídeo de saída
codec = cv2.VideoWriter_fourcc(*'XVID')
output_video = cv2.VideoWriter('output_video_path.mp4', codec, fps, (width, height))
import time
while True:
    # Lê o frame da captura
    ret, frame = captura.read()

    if not ret:
        break
    
    # Chama a função de estilo para modificar o frame
    inicio = time.time()
    frame = portal_img(frame)
    final = time.time()
    print(final - inicio)
    output_video.write(frame)
    # Mostra o frame estilizado em uma janela chamada "Estilo em Tempo Real"
    cv2.imshow('Estilo em Tempo Real', frame)

    # Verifica se a tecla 'q' foi pressionada para encerrar o loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libera a captura e fecha todas as janelas abertas
output_video.release()
cv2.destroyAllWindows()