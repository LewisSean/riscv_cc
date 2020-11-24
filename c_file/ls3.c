
int a = 1000;
int main(int c ,int b){
a = a + c * &b;
c = c * (a+b) + --b + b--;
int d = -c * b;
int kk = a > 1000? d : a;
if(a > 0 || a < 100){
c = c + 2*b;
}
else{
c = b + 2*c;
}

return c;
}