from gurobipy import *
import sys

class PhotoSlideShow:
    def __init__(self,file_name):
        self.photos = self.read_instance_from_file(file_name)
        self.M=len(self.photos)
        self.horizontal_photos,self.vertical_photos=self.countHorizontalVertical()
        self.H=len(self.horizontal_photos)
        self.V=len(self.vertical_photos)
        self.NH=self.H
        self.NV=int(self.V*(self.V-1)/2)
        self.N=self.NH+self.NV
        self.possible_slides=self.getPossibleSlides()
        self.same_photos=self.getSamePhotos()
        self.transition, self.transition_interest=self.calculateTransitionInterest()
    
    def read_instance_from_file(self,file_name: str):
        result=dict()
        try:
            with open('Instances\\' + file_name, 'r') as f:
                P = int(f.readline())
                photos = {}
                for i in range(P):
                    photo_text = f.readline()
                    photo_data = photo_text.split()
                    photos[i] = photo_data
                result = photos
        except FileNotFoundError as e:
            print(e.strerror)
        except Exception as e:
            print(e.values)
        else:
            pass
        return result

    def countHorizontalVertical(self):
        """Count horizontal and vertical phots"""
        horizontal_photos=dict()
        vertical_photos=dict()
        for id, photos in self.photos.items():
            if photos[0]=='H':
                horizontal_photos[id]=photos[2:]
            else:
                vertical_photos[id]=photos[2:]
        return horizontal_photos,vertical_photos
    
    def getPossibleSlides(self)->dict:
        """Define possible list of slides by considering horizontal and vertical photos"""
        result=dict()
        slide_index=0
        # Get possible slides from Horizontal photos
        for horizontal_photo_id in self.horizontal_photos.keys():
            result[slide_index]=[horizontal_photo_id]
            slide_index+=1
        
        # Get possible slides from Vertical photos
        vertical_photo_ids=[key for key in self.vertical_photos.keys()]
        for i in range(len(vertical_photo_ids)-1):
            for j in range (i+1,len(vertical_photo_ids)):
                first_photo_id=vertical_photo_ids[i]
                second_photo_id=vertical_photo_ids[j]
                result[slide_index]=[first_photo_id,second_photo_id]
                slide_index+=1
        return result

    def getSamePhotos(self)->tuplelist:
        """Get slides that have same photos"""
        result_list=list()
        possible_slide_list=[key for key in self.possible_slides.keys()]
        for i in range(self.H,len(possible_slide_list)-1):
            for j in range(i+1,len(possible_slide_list)):
                slide_1_photos=set(self.possible_slides[i])
                slide_2_photos=set(self.possible_slides[j])
                if len(slide_1_photos.intersection(slide_2_photos))>0:
                    result_list.append((i,j))
        return tuplelist(result_list)

    def calculateTransitionInterest(self)->multidict:
        """Calcualte Transition Interest between all possible slides"""
        result_dict=dict()
        possible_slide_list=[key for key in self.possible_slides.keys()]
        for i in range(0,len(possible_slide_list)-1):
            for j in range(i+1,len(possible_slide_list)):
                # Debug
                if i==1 and j==9:
                    print("Debug")
                slide_1_photos=self.possible_slides[possible_slide_list[i]]
                slide_2_photos=self.possible_slides[possible_slide_list[j]]
                slide_1_tags=set()
                for p in slide_1_photos:
                    for t in self.photos[p][2:]:
                        slide_1_tags.add(t)                
                slide_2_tags=set()
                for p in slide_2_photos:
                    for t in self.photos[p][2:]:
                        slide_2_tags.add(t)
                intersaction12=slide_1_tags.intersection(slide_2_tags)
                difference12=slide_1_tags.difference(slide_2_tags)
                difference21=slide_2_tags.difference(slide_1_tags)
                transition_interest=min(len(intersaction12),len(difference12),len(difference21))
                result_dict[(i,j)]=transition_interest
        return multidict(result_dict)


    def transform_tuple(self, t:tuple)->tuple:
        """Transform tuple indeces"""
        if(t[0]>t[1]):
            print("OK")
        min_index=min(t)
        max_index=max(t)
        return (min_index,max_index)

    def create_model(self):
        m = Model('photo slide show')
        # m.Params.WorkLimit = 30

        # Decision variables
        z = {}
        for i in range(self.N):
            for j in range(self.N):
                if i != j:
                    z[(i, j)] = m.addVar(vtype=GRB.BINARY, name='z' + str(i)+ ',' + str(j))

        # Constraints
        for sp in self.same_photos:
            i = sp[0]
            j = sp[1]
            m.addConstr(quicksum(quicksum(z[(a, b)] for b in range(self.N) 
                if b != a and ((a == i and b == j) or (a == j or b == i))) 
                for a in range(self.N)) <= 0, name='same photos')

        for i in range(self.N ):
            m.addConstr(quicksum(z[(i, j)] for j in range(self.N) if j != i) <= 1,
                        name='one slide is placed after slide i')

        for j in range(self.N):
            m.addConstr(quicksum(z[(i, j)] for i in range(self.N) if j != i) <= 1,
                        name='one slide is placed after slide j ')
        
        # for k in range(self.H):
        #     m.addConstr(quicksum(quicksum(z[(i, j)] 
        #                 for j in range(self.N) if j != i and (i==k or j==k)) 
        #                 for i in range(self.N))<= 2,
        #                             name='each slide is used at most once')
        for k in range(self.H):
            m.addConstr(quicksum(quicksum(z[(i, j)]
                        for j in range(self.H) if j != i and ((i==k and j!=k) or (i!=k or j==k))) 
                        for i in range(self.H))<= 2,
                                    name='each slide is used in at most one transition')

        m.update()
        m.setObjective(quicksum(quicksum(z[(i, j)]* self.transition_interest[self.transform_tuple((i, j))]
                        for j in range(self.N) if j != i) for i in range(self.N)), sense=GRB.MAXIMIZE)

        return m
    
    def solve_problem(self,m):
        m.optimize()
        m.printAttr('X')
       

        # Extract solution as a list of slides
        slide_pair_queue=[]
        for v in m.getVars():
            if int(v.X):
                slide_indecies=v.VarName[1:].split(',')
                slide_pair_queue.append(tuple([int(i) for i in slide_indecies]))

        # Test
        slide_pair_queue_set=set()
        for sp in slide_pair_queue:
            slide_pair_queue_set.add(sp[0])
            slide_pair_queue_set.add(sp[1])

        slide_list=list()
        current_slide1,current_slide2=slide_pair_queue.pop(0)
        slide_list.append(current_slide1)
        slide_list.append(current_slide2)
        previous_slide1, previous_slide2=current_slide1,current_slide2
        count_push_back=0
        count_push_back_reset=False
        while len(slide_pair_queue)>0:
            current_slide_transition=slide_pair_queue.pop(0)
            current_slide1,current_slide2=current_slide_transition
            if len(slide_pair_queue)==0 and previous_slide2!=current_slide1:
                slide_list.append(current_slide1)
                slide_list.append(current_slide2)
            elif previous_slide2==current_slide1 or count_push_back_reset:
                if previous_slide2==current_slide1:
                    slide_list.append(current_slide2)
                else:
                    slide_list.append(current_slide1)
                    slide_list.append(current_slide2)
                previous_slide1, previous_slide2=current_slide1,current_slide2
                count_push_back=0
                count_push_back_reset=False
            elif count_push_back==len(slide_pair_queue):
                count_push_back=0
                count_push_back_reset=True
                slide_pair_queue.append(current_slide_transition)
            else:
                slide_pair_queue.append(current_slide_transition)
                count_push_back+=1
                count_push_back_reset=False
            if(slide_list[len(slide_list)-1]==73):
                print("test")
        objective_value=m.objVal
        
        # Test2
        if len(slide_list)==len(slide_pair_queue_set):
            print("OK")
        else:
            print("NOT OK")
        # Test2
        slide_set=set(slide_list)
        if len(slide_list)==len(slide_set):
            print("Unique OK")
        else:
            print("Not unique")
        return slide_list, objective_value

    def save_solution_to_file(self,slide_list:list,objective_value:float):
        solution_text=str(len(slide_list))+'\n'
        for s in slide_list:
            current_slide_photos=self.possible_slides[s]
            if len(current_slide_photos)==1:
                solution_text=solution_text+str(current_slide_photos[0])+'\n'
            else:
                solution_text=solution_text+str(current_slide_photos[0])+' '+str(current_slide_photos[1])+'\n'
        print("Objective value: {}".format(objective_value))
        print("Num slides: {}".format(len(slide_list)))
        print(slide_list)
        print(solution_text)
        output_file_name=file_name+'_solution_'+str(objective_value)+'.txt'
        with open("Solutions\\"+output_file_name,'w') as f:
            f.write(solution_text)

def help_function():
    """Define help function"""
    print("The solver should be callde usign the command 'python photo_slideshow_solver.py instance_name.txt'")
    print("Example: python photo_slideshow_solver.py c_memorable_moments_50.txt")

if __name__=="__main__":
    """ Create an instance of the model and solve the problem"""
    arguments=sys.argv
    if len(arguments)!=2:
        help_function()
        exit()
    else:
        file_name = arguments[1]
        ps=PhotoSlideShow(file_name)
        model=ps.create_model()
        slide_list, objective_value=ps.solve_problem(model)
        ps.save_solution_to_file(slide_list,objective_value)
    # file_name = "c_memorable_moments_20.txt"
    # ps=PhotoSlideShow(file_name)
    # model=ps.create_model()
    # slide_list, objective_value=ps.solve_problem(model)
    # ps.save_solution_to_file(slide_list,objective_value)