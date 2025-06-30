
Certainly! Let's look at some **illustrative biased estimators** in the context of a Gaussian distribution $X \sim \mathcal{N}(\mu, \sigma^2)$.

---

### 🔹 Scenario:

You observe i.i.d. samples $X_1, X_2, \dots, X_n \sim \mathcal{N}(\mu, \sigma^2)$. You wish to estimate $\mu$ and $\sigma^2$.

---

## 🟥 1. **Biased Estimator of the Mean**

### Estimator:

$$
\hat{\mu}_{\text{biased}} = \frac{1}{n+1} \sum_{i=1}^n X_i
$$

### Bias:

$$
\mathbb{E}[\hat{\mu}_{\text{biased}}] = \frac{1}{n+1} \sum_{i=1}^n \mathbb{E}[X_i] = \frac{n}{n+1} \mu
$$

$$
\Rightarrow \text{Bias} = \mathbb{E}[\hat{\mu}_{\text{biased}}] - \mu = \left( \frac{n}{n+1} - 1 \right)\mu = -\frac{1}{n+1} \mu
$$

✅ Biased **low**.

---

## 🟧 2. **Biased Estimator of the Variance**

### Estimator (commonly used naive one):

$$
\hat{\sigma}^2_{\text{biased}} = \frac{1}{n} \sum_{i=1}^n (X_i - \bar{X})^2
$$

where $\bar{X} = \frac{1}{n} \sum X_i$.

### Bias:

This underestimates the true variance. The **unbiased** version divides by $n - 1$, not $n$.

$$
\mathbb{E}[\hat{\sigma}^2_{\text{biased}}] = \frac{n-1}{n} \sigma^2
$$

$$
\Rightarrow \text{Bias} = -\frac{1}{n} \sigma^2
$$

✅ This is one of the most well-known biased estimators.

---

## 🟨 3. **Truncated Estimator of the Mean**

Let’s say you drop values above some threshold to reduce outliers:

$$
\hat{\mu}_{\text{trunc}} = \frac{1}{n} \sum_{i=1}^n X_i \cdot \mathbf{1}_{|X_i| < T}
$$

where $\mathbf{1}$ is the indicator function.

This will **bias the mean toward zero**, since you're ignoring high-magnitude values (especially if $\mu \neq 0$).

---

## 🟦 Summary Table

| Estimator Type        | Formula                                     | Bias                   |        |                             |
| --------------------- | ------------------------------------------- | ---------------------- | ------ | --------------------------- |
| Mean (bad scaling)    | $\frac{1}{n+1} \sum X_i$                    | $-\frac{1}{n+1}\mu$    |        |                             |
| Variance (div by $n$) | $\frac{1}{n} \sum (X_i - \bar{X})^2$        | $-\frac{1}{n}\sigma^2$ |        |                             |
| Truncated mean        | ( \frac{1}{n} \sum X\_i \cdot \mathbf{1}\_{ | X\_i                   | < T} ) | Biased low (depends on $T$) |

---

Would you like to visualize the bias using simulation or distribution curves?



Let's now **illustrate the biased and unbiased variance estimators** mathematically.

---

### 🔷 Setup

Let $X_1, \dots, X_n$ be i.i.d. samples from a distribution with mean $\mu$ and variance $\sigma^2$.

Define:

* Sample mean:

  $$
  \bar{X} = \frac{1}{n} \sum_{i=1}^n X_i
  $$

---

## 🟧 Biased Estimator

$$
\hat{\sigma}^2_{\text{biased}} = \frac{1}{n} \sum_{i=1}^n (X_i - \bar{X})^2
$$

### Expectation:

We compute:

$$
\mathbb{E}\left[\hat{\sigma}^2_{\text{biased}}\right] = \frac{1}{n} \sum_{i=1}^n \mathbb{E}[(X_i - \bar{X})^2]
$$

This expands using the variance decomposition identity:

$$
\mathbb{E}[(X_i - \bar{X})^2] = \mathbb{E}[(X_i - \mu)^2] - \mathbb{E}[(\bar{X} - \mu)^2]
$$

After derivation (detailed below if requested), we get:

$$
\mathbb{E}\left[\hat{\sigma}^2_{\text{biased}}\right] = \frac{n-1}{n} \sigma^2
$$

Thus:

$$
\text{Bias} = \mathbb{E}[\hat{\sigma}^2_{\text{biased}}] - \sigma^2 = -\frac{1}{n} \sigma^2
$$

---

## ✅ Unbiased Estimator

$$
\hat{\sigma}^2_{\text{unbiased}} = \frac{1}{n-1} \sum_{i=1}^n (X_i - \bar{X})^2
$$

Then:

$$
\mathbb{E}[\hat{\sigma}^2_{\text{unbiased}}] = \sigma^2
$$

So it's unbiased.

---

### 📌 Why the Bias Happens

When estimating variance, we subtract the estimated mean $\bar{X}$, which itself depends on the data. This introduces dependency and "costs" 1 degree of freedom, hence dividing by $n$ underestimates the true variance.

---

Would you like a derivation for why $\mathbb{E}[\sum (X_i - \bar{X})^2] = (n-1)\sigma^2$?


