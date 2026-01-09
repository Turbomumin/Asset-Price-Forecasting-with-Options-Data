# Asset-Price-Forecasting-with-Options-Data

Will write more as I work along with this little project.

Options markets allow firms and people to make trades on volatility and asset price movements beyond the underlying tradeable asset. Based on the pricing of these derivatives, we can find aggregated implications on the price movements of the underlying assets. By calculating implied probabilities of options expiring ATM or ITM, and combining these implied probabilities within a whole option chain, one could forecast price movements of the underlying assets based on market pricing of options. 

What I aim to explore is how reliable this forecasting is. With historical option prices from WRDS, I could analyse what signals can be extracted from this method for options trading and underlying trading.

## Step by step description of what the code does now

Option chain is retrieved via Yahoo finance. The data is bound to have some incosistencies so options not fulfilling the certain criteria are filtered out. The criteria focused on are regarding volume, bid/ask prices, and days to expiry. Options where (1) traded volume is less than 10, (2) bid or ask prices are 0, or (3) expiring today are removed. This removes a significant amount of options but leaves enough to reliably continue calculations.

For calculting option prices, implied volatilities etc., it is important to use a reliable interest rate. One method is to set the interest rate to a static floating number, (i.e 3%). The method I decided to use is to calculate box spreads and from the given prices, an practical annual interest rate can be derived. Options used are filtered for, in addition to earlier filtering criteria, days to expiry above 90. Options which after filtering dont have both a put and a call price are also removed. Hundreds of box spreads are calculated and an average is calculated.

Those interest rates are used to calculate delta for each option, which can be interpreted as the probability of expiring ATM or ITM.

## Next steps

The calculated probabilities cant be used to calculate probabilities of the underlying being at certain price levels at given times in the future, so some additional techniques are going to be used. See Stochastic Volatility Inspired models and qubic splines. SVI provides the necessary analytical smoothness to extract a Risk-Neutral Density (RND) without the noise inherent in raw SPX market quotes.

Then, the Breeden-Litzberger formula will be used to extract implied risk neutral densities. 
