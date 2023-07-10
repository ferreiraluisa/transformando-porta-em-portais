#@title Inferencer
#CÓDIGO EXTRAÍDO DE https://github.com/ryanwongsa/Real-time-multi-style-transfer
class Inferencer(object):
    def __init__(self, pastiche_model,device,image_size):
        self.pastichemodel = pastiche_model
        self.device = device

        self.pastichemodel = self.pastichemodel.to(self.device)
        self.pastichemodel = self.pastichemodel.eval()

        self.mean = [0.485, 0.456, 0.406]
        self.std=[0.229, 0.224, 0.225]

        self.transformer = transforms.Compose([
        transforms.Resize(image_size),
        transforms.ToTensor(),
            transforms.Normalize(mean=self.mean,
                                 std=self.std)
        ])


    def load_model_weights(self, dir_model):
        self.pastichemodel.load_state_dict(torch.load(dir_model))

    def eval_image(self, img, style_num,style_num2=None,alpha=None):
        out = self.transformer(img)
        res = self.pastichemodel(out.unsqueeze(0).to(self.device),style_num,style_num2,alpha)
        res_img = Image.fromarray(np.uint8(np.moveaxis(res[0].cpu().detach().numpy()*255.0, 0, 2)))
        return res_img