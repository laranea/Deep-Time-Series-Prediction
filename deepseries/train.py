# encoding: utf-8
"""
@author : zhirui zhou
@contact: evilpsycho42@gmail.com
@time   : 2020/4/1 17:03
"""
import os
import torch
from torch.utils.tensorboard import SummaryWriter
from datetime import datetime
import logging
import numpy as np
import time


class Learner:

    def __init__(self, model, optimizer, loss_fn, root_dir, log_interval=4, lr_scheduler=None, grad_clip=5):
        self.model = model
        self.optimizer = optimizer
        self.loss_fn = loss_fn
        self.lr_scheduler = lr_scheduler
        self.grad_clip = grad_clip

        self.root_dir = root_dir
        self.log_dir = os.path.join(root_dir, 'logs')
        self.model_dir = os.path.join(root_dir, 'checkpoints')
        for i in [self.root_dir, self.log_dir, self.model_dir]:
            if not os.path.exists(i):
                os.mkdir(i)
        self.epochs = 0
        self.losses = []
        self.init_logging()
        self.log_interval = log_interval

    def init_logging(self):

        # exist_logger = logging.Logger.manager.loggerDict()
        # if 'deepseries' not in exist_logger:

        date_str = datetime.now().strftime('%Y-%m-%d_%H-%M')
        log_file = 'log_{}.txt'.format(date_str)
        logging.basicConfig(
            filename=os.path.join(self.log_dir, log_file),
            level=logging.INFO,
            format='[[%(asctime)s]] %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p'
        )
        logging.getLogger().addHandler(logging.StreamHandler())

    def fit(self, max_epochs, train_dl, valid_dl, early_stopping=True, patient=10, start_save=-1):
        with SummaryWriter(self.log_dir) as writer:
            # writer.add_graph(self.model)
            logging.info(f"start training >>>>>>>>>>>  "
                         f"see log: tensorboard --logdir {self.log_dir}")
            best_score = np.inf
            bad_epochs = 0
            global_steps = 0
            for epoch in range(1, max_epochs+1):
                time_start = time.time()
                self.model.train()
                train_loss = 0
                for i, (x, y, w) in enumerate(train_dl):
                    loss = self.loss_batch(x, y, w)
                    writer.add_scalar("Loss/train", loss, global_steps)
                    global_steps += 1
                    train_loss += loss
                    if global_steps % self.log_interval == 0:
                        logging.info(f"epoch {epoch} / {max_epochs}, batch {i/len(train_dl)*100:3.0f}%, "
                                     f"train loss {train_loss / (i+1):.4f}")
                valid_loss = 0
                self.model.eval()
                for x, y, w in valid_dl:
                    loss = self.eval_batch(x, y, w)
                    valid_loss += loss / len(valid_dl)
                writer.add_scalar("Loss/valid", valid_loss, global_steps)
                epoch_use_time = (time.time() - time_start) / 60
                logging.info(f"epoch {epoch} / {max_epochs}, batch 100%, "
                             f"train loss {train_loss / len(train_dl):.4f}, valid loss {valid_loss:.4f}, "
                             f"cost time {epoch_use_time:.1f} minute")

                self.losses.append(valid_loss)

                if epoch >= start_save:
                    self.save()
                if early_stopping:
                    if self.epochs > 1:
                        if valid_loss > best_score:
                            bad_epochs += 1
                        else:
                            bad_epochs = 0
                        if bad_epochs >= patient:
                            print("early stopping!")
                            break
                best_score = min(self.losses)
                if self.lr_scheduler is not None:
                    self.lr_scheduler.step()
                writer.add_scalar('lr', self.optimizer.param_groups[0]['lr'], global_steps)
                self.epochs += 1
            logging.info(f"training finished, best epoch {np.argmin(self.losses)}, best valid loss {best_score:.4f}")

    def loss_batch(self, x, y, w):
        self.optimizer.zero_grad()
        if isinstance(x, dict):
            y_hat = self.model(**x)
        else:
            y_hat = self.model(*x)
        loss = self.loss_fn(y_hat, y, w)  # / y.shape[0]  # add gradient normalize
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.grad_clip)
        self.optimizer.step()
        return loss.item()

    def eval_batch(self, x, y, w):
        with torch.no_grad():
            if isinstance(x, dict):
                y_hat = self.model(**x)
            else:
                y_hat = self.model(*x)
            loss = self.loss_fn(y, y_hat, w)  # / y.shape[0]  # add gradient normalize
        return loss.item()

    def load(self, model_checkpoint_path):
        checkpoint = torch.load(model_checkpoint_path)
        self.model.load_state_dict(checkpoint['model'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epochs = checkpoint['epochs']
        self.lr_scheduler = checkpoint['lr_scheduler']

    def save(self):
        checkpoint = {
            "model": self.model.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "epochs": self.epochs,
            'lr_scheduler': self.lr_scheduler,
        }

        name = f"model-epoch-{self.epochs}.pkl"
        torch.save(checkpoint, os.path.join(self.model_dir, name))
