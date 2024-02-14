import tensorflow as tf

# SAR2SAR: https://doi.org/10.1109/JSTARS.2021.3071864


# Nearest-neighbor upscaling layer.
def upscale2d(x, factor=2):
    assert isinstance(factor, int) and factor >= 1
    if factor == 1:
        return x
    with tf.compat.v1.variable_scope("Upscale2D"):
        s = x.shape
        x = tf.reshape(x, [-1, s[1], 1, s[2], 1, s[3]])
        x = tf.tile(x, [1, 1, factor, 1, factor, 1])
        x = tf.reshape(x, [-1, s[1] * factor, s[2] * factor, s[3]])
        return x


regularizer = tf.keras.regularizers.l2(0.5 * (0.1))


def autoencoder(x, width=256, height=256, **_kwargs):
    """if config.get_nb_channels() == 1:
        x.set_shape([None, 1, height, width])
    else:
        x.set_shape([None, 3, height, width])"""
    x.set_shape([None, height, width, 1])

    skips = [x]

    n = x
    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(48, 3, padding="same", name="enc_conv0")(n)
    )
    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(48, 3, padding="same", name="enc_conv1")(n)
    )
    n = tf.keras.layers.MaxPooling2D(pool_size=(2, 2), strides=(2, 2), padding="same")(
        n
    )
    skips.append(n)

    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(48, 3, padding="same", name="enc_conv2")(n)
    )
    n = tf.keras.layers.MaxPooling2D(pool_size=(2, 2), strides=(2, 2), padding="same")(
        n
    )
    skips.append(n)

    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(48, 3, padding="same", name="enc_conv3")(n)
    )
    n = tf.keras.layers.MaxPooling2D(pool_size=(2, 2), strides=(2, 2), padding="same")(
        n
    )
    skips.append(n)

    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(48, 3, padding="same", name="enc_conv4")(n)
    )
    n = tf.keras.layers.MaxPooling2D(pool_size=(2, 2), strides=(2, 2), padding="same")(
        n
    )
    skips.append(n)

    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(48, 3, padding="same", name="enc_conv5")(n)
    )
    n = tf.keras.layers.MaxPooling2D(pool_size=(2, 2), strides=(2, 2), padding="same")(
        n
    )
    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(48, 3, padding="same", name="enc_conv6")(n)
    )

    # -----------------------------------------------
    n = upscale2d(n)
    n = tf.keras.layers.Concatenate(axis=-1)([n, skips.pop()])
    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(96, 3, padding="same", name="dec_conv5")(n)
    )
    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(96, 3, padding="same", name="dec_conv5b")(n)
    )

    n = upscale2d(n)
    n = tf.keras.layers.Concatenate(axis=-1)([n, skips.pop()])
    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(96, 3, padding="same", name="dec_conv4")(n)
    )
    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(96, 3, padding="same", name="dec_conv4b")(n)
    )

    n = upscale2d(n)
    n = tf.keras.layers.Concatenate(axis=-1)([n, skips.pop()])
    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(96, 3, padding="same", name="dec_conv3")(n)
    )
    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(96, 3, padding="same", name="dec_conv3b")(n)
    )

    n = upscale2d(n)
    n = tf.keras.layers.Concatenate(axis=-1)([n, skips.pop()])
    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(96, 3, padding="same", name="dec_conv2")(n)
    )
    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(96, 3, padding="same", name="dec_conv2b")(n)
    )

    n = upscale2d(n)
    n = tf.keras.layers.Concatenate(axis=-1)([n, skips.pop()])
    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(64, 3, padding="same", name="dec_conv1a")(n)
    )
    n = tf.keras.layers.LeakyReLU(alpha=0.1)(
        tf.keras.layers.Conv2D(32, 3, padding="same", name="dec_conv1b")(n)
    )

    n = tf.keras.layers.Conv2D(1, 3, padding="same", name="dec_conv1")(n)

    return x - n
