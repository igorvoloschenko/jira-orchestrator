#!/usr/bin/env python3

import sys
from argparse import ArgumentParser
import logging
import config
import secret
import handler

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--config", default="config.yaml", 
        help="Path to configuration file. Default: config.yaml")
    args = parser.parse_args()
    
    try:
        cfg = config.Get(args.config)
        if config.Validate(cfg):
            if "logging" in cfg:
                logging.basicConfig(**cfg['logging'])

            secret_cfg = cfg.get("secret")
            if secret_cfg:
                secret_provider = secret.ProviderNew(secret_cfg)
            else:
                secret_provider = secret.Secret()
            
            # Заполнение переменных {{ secret.<nameseceret> }} в конфигурации 
            # значениями из secret_provider
            cfg = config.SecretFill(cfg, secret_provider)

            handler.Run(cfg)

    except Exception as e:
        logging.error(e)
        sys.exit(1)

