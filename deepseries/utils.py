# encoding: utf-8
# Author: 周知瑞
# Mail: evilpsycho42@gmail.com


class HyperParameters(dict):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __getattr__(self, item):
        return self.get(item)

    def __setattr__(self, key, value):
        self[key] = value


class EMA:
    # TODO
    """Weights Exponential Moving Average.

    Args:
        model(torch.nn.module).
        decay(float).

    Examples:

        ema = EMA(model, 0.99)

        # train stage
        opt.step()
        ema.update()

        # eval stage
        ema.apply_shadow()
        model.predict(...)
        ema.restore()
    """

    def __init__(self, model, decay):
        self.model = model
        self.decay = decay
        self.shadow = {}
        self.backup = {}
        self.register()

    def register(self):
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                self.shadow[name] = param.data.clone()

    def update(self):
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                assert name in self.shadow
                new_average = (1.0 - self.decay) * param.data + self.decay * self.shadow[name]
                self.shadow[name] = new_average.clone()

    def apply_shadow(self):
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                assert name in self.shadow
                self.backup[name] = param.data
                param.data = self.shadow[name]

    def restore(self):
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                assert name in self.backup
                param.data = self.backup[name]
        self.backup = {}
