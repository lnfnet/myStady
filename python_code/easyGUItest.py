#incoding= utf-8
import sys
import easygui as g

reply = g.choicebox("Do you like to eat fish?", choices=["Yes","No","Only on Friday"])
print(reply)

g.egdemo()
g.ynbox('我能续续么？','标题',('是','否'))
g.msgbox('This is a basic message box.', '标题')
g.buttonbox('Click on your favorite flavor.', '你的最爱', ('Chocolate', 'Vanilla', 'Strawberry'))


while 1:
    g.msgbox("Hello, world!")

    msg ="What is your favorite flavor?"
    title = "Ice Cream Survey"
    choices = ["Vanilla", "Chocolate", "Strawberry", "Rocky Road"]
    choice = g.choicebox(msg, title, choices)

    # note that we convert choice to string, in case
    # the user cancelled the choice, and we got None.
    g.msgbox("You chose: " + str(choice), "Survey Result")

    msg = "Do you want to continue?"
    title = "Please Confirm"
    if g.ccbox(msg, title):     # show a Continue/Cancel dialog
        pass  # user chose Continue
    else:
        sys.exit(0)           # user chose Cancel
