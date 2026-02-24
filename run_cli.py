#!/usr/bin/env python3
import argparse
import csv
import os
import requests
import torch
from PIL import Image
from clip_interrogator import Interrogator, Config, list_clip_models

def inference(ci, images, mode):
    if mode == 'best':
        return ci.interrogate(images)
    elif mode == 'classic':
        return ci.interrogate_classic(images)
    elif mode == 'fast':
        return ci.interrogate_fast(images)
    elif mode == 'negative':
        return ci.interrogate_negative(images)
    else:
        return ci.interrogate_orthogonal_fast(images)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clip', default='ViT-L-14-336/openai', help='name of CLIP model to use')
    parser.add_argument('-d', '--device', default='auto', help='device to use (auto, cuda or cpu)')
    parser.add_argument('-f', '--folder', help='path to folder of images')
    parser.add_argument('-i', '--image', help='image file or url')
    parser.add_argument('-m', '--mode', default='best', help='best, classic, fast, negative or orthogonal')
    parser.add_argument('-n', '--noblip', action='store_true', help='only CLIP for captioning, faster')
    parser.add_argument('-q', '--quiet', action='store_true', help='reduce console spam')
    parser.add_argument("--lowvram", action='store_true', help="Optimize settings for low VRAM")

    args = parser.parse_args()
    if not args.folder and not args.image:
        parser.print_help()
        exit(1)

    if args.folder is not None and args.image is not None:
        print("Specify a folder or batch processing or a single image, not both")
        exit(1)

    # validate clip model name
    models = list_clip_models()
    if args.clip not in models:
        print(f"Could not find CLIP model {args.clip}!")
        print(f"    available models: {models}")
        exit(1)

    # select device
    if args.device == 'auto':
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        if not torch.cuda.is_available():
            print("CUDA is not available, using CPU. Warning: this will be very slow!")
    else:
        device = torch.device(args.device)

    # generate a nice prompt
    config = Config(device=device, clip_model_name=args.clip)
    if args.lowvram:
        config.apply_low_vram_defaults()
    if args.noblip:
        config.caption_model_name = None
    config.quiet = args.quiet
    if args.quiet:
        import warnings
        warnings.filterwarnings("ignore")
    ci = Interrogator(config)

    # process single image
    if args.image is not None:
        image_path = args.image
        if str(image_path).startswith('http://') or str(image_path).startswith('https://'):
            image = Image.open(requests.get(image_path, stream=True).raw).convert('RGB')
        else:
            image = Image.open(image_path).convert('RGB')
        if not image:
            print(f'Error opening image {image_path}')
            exit(1)
        if args.mode == 'best':
            gen = inference(ci, [image], args.mode)
            if not args.noblip:
                print('Preliminary caption: ', next(gen)[0])
            result = next(gen)
            if not args.quiet and not args.noblip:
                print('Final result:')
            print(result[0])
            print(f'Certainty: {result[1]:.3f}')
        else:
            print(inference(ci, [image], args.mode)[0])

    # process folder of images
    elif args.folder is not None:
        if not os.path.exists(args.folder):
            print(f'The folder {args.folder} does not exist!')
            exit(1)

        files = [f for f in os.listdir(args.folder) if f.endswith('.jpg') or f.endswith('.png') or f.endswith('.jpeg') or f.endswith('.bmp') or f.endswith('.webp') or f.endswith('.gif')]
        images = [Image.open(os.path.join(args.folder, file)).convert('RGB') for file in files]

        if args.mode == 'best':
            gen = inference(ci, images, args.mode)
            if not args.noblip:
                print('Preliminary caption: ', next(gen)[0])
            result = next(gen)
            if not args.quiet and not args.noblip:
                print('Final result:')
            print(result[0])
            print(f'Certainty: {result[1]:.3f}')
            if not args.quiet:
                print('Displaying most representative image...')
            result[2].show()
            result = result[0]
        else:
            result = inference(ci, images, args.mode)[0]
            print(result)

        if len(result):
            csv_path = os.path.join(args.folder, 'desc.csv')
            exists = os.path.exists(os.path.join(args.folder, 'desc.csv'))
            with open(csv_path, 'a', encoding='utf-8', newline='') as f:
                w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                if not exists:
                    w.writerow(['mode','prompt'])
                w.writerow([args.mode,result])
            if not config.quiet:
                print(f"\n\n\n\nSaved to {csv_path}, enjoy!")

if __name__ == "__main__":
    main()
