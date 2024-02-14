from sentinel_1.sar2sar_utils import *
from sentinel_1.sar2sar_u_net import *
import os
import sys

# SAR2SAR: https://doi.org/10.1109/JSTARS.2021.3071864


class sar2sar_denoiser(object):
    def __init__(self, sess, input_c_dim=1):
        self.sess = sess
        self.input_c_dim = input_c_dim
        self.Y_ = tf.compat.v1.placeholder(
            tf.float32, [None, None, None, self.input_c_dim], name="clean_image"
        )
        self.Y = autoencoder((self.Y_))
        init = tf.compat.v1.global_variables_initializer()
        self.sess.run(init)
        print("# Initialized model successfully...")

    def load(self, checkpoint_dir):
        print("# Reading checkpoint...")
        saver = tf.compat.v1.train.Saver()
        ckpt = tf.train.get_checkpoint_state(checkpoint_dir)
        if ckpt and ckpt.model_checkpoint_path:
            full_path = tf.train.latest_checkpoint(checkpoint_dir)
            saver.restore(self.sess, full_path)
            return True
        else:
            return False

    def check_if_denoised_exists(self, noisy_img_path, save_dir):
        filename = os.path.basename(noisy_img_path)

        filename = save_dir + filename
        if os.path.isfile(filename):
            return True

        return False

    def test(self, test_files, ckpt_dir, save_dir, dataset_dir, stride):
        tf.compat.v1.initialize_all_variables().run()

        assert len(test_files) != 0, "# No testing data!"

        load_model_status = self.load(ckpt_dir)
        assert load_model_status == True, "# Weights failed to load!"
        print("# Weights loaded successfully...")

        os.makedirs(save_dir, exist_ok=True)
        print("# Denoising files...")
        for i, idx in enumerate(range(len(test_files))):
            print("# " + str(i + 1) + " / " + str(len(test_files)), end="\r")

            # # only use this if process has failed and good densoised npy are lying in the folder
            # if self.check_if_denoised_exists(test_files[idx], save_dir):
            #     print("GOTCHA!!!")
            #     continue

            real_image = load_sar_images(test_files[idx]).astype(np.float32) / 255.0

            pat_size = 256  # Pad the image
            im_h = np.size(real_image, 1)
            im_w = np.size(real_image, 2)

            count_image = np.zeros(real_image.shape)
            output_clean_image = np.zeros(real_image.shape)

            # Pad height
            if im_h == pat_size:
                x_range = list(np.array([0]))
            else:
                x_range = list(range(0, im_h - pat_size, stride))
                if (x_range[-1] + pat_size) < im_h:
                    x_range.extend(range(im_h - pat_size, im_h - pat_size + 1))

            # Pad width
            if im_w == pat_size:
                y_range = list(np.array([0]))
            else:
                y_range = list(range(0, im_w - pat_size, stride))
                if (y_range[-1] + pat_size) < im_w:
                    y_range.extend(range(im_w - pat_size, im_w - pat_size + 1))

            for x in x_range:
                for y in y_range:
                    tmp_clean_image = self.sess.run(
                        [self.Y],
                        feed_dict={
                            self.Y_: real_image[
                                :, x : x + pat_size, y : y + pat_size, :
                            ]
                        },
                    )
                    output_clean_image[:, x : x + pat_size, y : y + pat_size, :] = (
                        output_clean_image[:, x : x + pat_size, y : y + pat_size, :]
                        + tmp_clean_image
                    )
                    count_image[:, x : x + pat_size, y : y + pat_size, :] = count_image[
                        :, x : x + pat_size, y : y + pat_size, :
                    ] + np.ones((1, pat_size, pat_size, 1))
            output_clean_image = output_clean_image / count_image

            noisyimage = denormalize_sar(real_image)

            outputimage = denormalize_sar(output_clean_image)

            imagename = os.path.basename(test_files[idx])
            save_sar_images(outputimage, noisyimage, imagename, save_dir)
