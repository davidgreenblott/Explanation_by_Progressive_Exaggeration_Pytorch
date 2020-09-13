# Description: read data from configs and preprocess it

import os

import pandas as pd
import pytorch_lightning as pl
import torch
import yaml
from PIL import Image
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms


# Think about
# output_dir = os.path.join(config['log_dir'], config['name'])

# Read data file = df.iloc: popping attrubutes by their name

# Убрать .npy файлы!

class DataModule(pl.LightningModule):
    class _Dataset(Dataset):
        def __init__(self, csv_data, im_folder, transforms, shuffle):
            self.transforms = transforms
            self.im_folder = im_folder

            self.data = csv_data
            if shuffle:
                self.data = self.data.sample(frac=1)

        def __getitem__(self, item):
            # TODO(check outputting labels as 1D tensors)
            image_path, labels = self.data.iloc[item]

            image_path = os.path.join(self.im_folder, image_path)

            image = Image.open(image_path, mode='RGB')

            if self.transforms is not None:
                image = self.transforms(image)

            return image, torch.tensor(labels)

        def __len__(self):
            return self.data.shape[0]

    def __init__(self, config_path='configs/celebA_YSBBB_Classifier.yaml'):
        super().__init__()

        self.config = yaml.load(config_path)
        print("Config  file:", self.config, sep='\n')

        self.image_dir = self.config['image_dir']
        self.data_path = self.config['image_label_dict']
        self.batch_size = self.config['batch_size']

        self.transforms = transforms.Compose([
            # Input PIL Image
            transforms.CenterCrop(128),
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.5, 0.5, 0.5), std=[2, 2, 2])
        ])

        assert (os.path.isdir(self.image_dir), f"Check image path:{self.image_dir}!")
        assert (os.path.isfile(self.data_path), f"File {self.data_path} is not found!")

    # On one CPU, not paralleled
    def prepare_data(self):
        data = pd.read_csv(self.data_path)

        # They don't have test data, only val data, why?
        train_data, val_data = train_test_split(data, test_size=0.33)

        self.train_dataset = DataModule._Dataset(train_data, self.image_dir, self.transforms, True)
        self.val_dataset = DataModule._Dataset(val_data, self.image_dir, self.transforms, False)

    def train_dataloader(self):
        return DataLoader(self.train_dataset, self.batch_size, True)

    def val_dataloader(self):
        return DataLoader(self.val_dataset, self.batch_size, False)
