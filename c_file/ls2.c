int main(){
int a = 100;
int c = 200;
int b = a + c;
if( b < 1000){
a++;
}
else if(b > 200){
b = b + 1;
}
else{
b = b+2;
}
while(b < 4) {
b++;
a++;
}
do{
c = c + 1;
a = a +1;
}while(b > 100);
return b;
}